# frozen_string_literal: true

require "tempfile"
require "timeout"

module DiscoursePdfSanitizer
  class Error < StandardError
  end

  class InvalidPdfError < Error
  end

  class DependencyError < Error
  end

  class SanitizationError < Error
  end

  class SanitizationTimeoutError < Error
  end

  class UploadSanitizer
    PDF_HEADER_BYTES = 1024
    LOG_LIMIT_BYTES = 2000
    PYTHON_ENV = "DISCOURSE_PDF_SANITIZER_PYTHON"

    class << self
      def sanitize!(file, runner: CommandRunner.new)
        validate_input!(file)

        Tempfile.create(%w[discourse-pdf-sanitized .pdf]) do |output|
          output.binmode
          runner.run(
            input_path: file.path,
            output_path: output.path,
            timeout_seconds: SiteSetting.discourse_pdf_sanitizer_timeout_seconds,
            max_output_bytes: SiteSetting.max_attachment_size_kb.kilobytes,
          )
          validate_output!(output)
          replace_input!(file, output)
        end

        file
      end

      private

      def validate_input!(file)
        raise InvalidPdfError, "input is not a readable file" unless file.respond_to?(:path)
        raise InvalidPdfError, "input is not a regular file" unless File.file?(file.path)

        File.open(file.path, "rb") do |input|
          header = input.read(PDF_HEADER_BYTES).to_s
          raise InvalidPdfError, "PDF header is missing" if header.exclude?("%PDF-")
        end
      end

      def validate_output!(output)
        output.flush
        raise SanitizationError, "sanitizer produced an empty file" unless File.size?(output.path)

        output.rewind
        header = output.read(PDF_HEADER_BYTES).to_s
        raise SanitizationError, "sanitizer produced a non-PDF file" if header.exclude?("%PDF-")
      end

      def replace_input!(file, output)
        output.rewind
        file.rewind
        file.truncate(0)
        IO.copy_stream(output, file)
        file.flush
        file.fsync
        file.rewind
      end
    end

    class CommandRunner
      def run(input_path:, output_path:, timeout_seconds:, max_output_bytes:)
        stdout = Tempfile.new("discourse-pdf-sanitizer-stdout")
        stderr = Tempfile.new("discourse-pdf-sanitizer-stderr")
        pid =
          spawn_process(
            input_path:,
            output_path:,
            stdout:,
            stderr:,
            timeout_seconds:,
            max_output_bytes:,
          )

        status = wait_for(pid, timeout_seconds)
        return if status.success?

        raise SanitizationError,
              "sanitizer exited with status #{status.exitstatus}: #{read_log(stderr)}"
      rescue Errno::ENOENT => error
        raise DependencyError, "Python runtime was not found: #{error.message}"
      ensure
        stdout&.close!
        stderr&.close!
      end

      private

      def spawn_process(
        input_path:,
        output_path:,
        stdout:,
        stderr:,
        timeout_seconds:,
        max_output_bytes:
      )
        Process.spawn(
          python_path,
          "-I",
          script_path,
          input_path,
          output_path,
          in: File::NULL,
          out: stdout.path,
          err: stderr.path,
          pgroup: true,
          rlimit_cpu: timeout_seconds + 1,
          rlimit_fsize: max_output_bytes,
        )
      end

      def wait_for(pid, timeout_seconds)
        Timeout.timeout(timeout_seconds) { Process.wait2(pid).last }
      rescue Timeout::Error
        terminate(pid)
        raise SanitizationTimeoutError, "sanitizer exceeded #{timeout_seconds} seconds"
      end

      def terminate(pid)
        Process.kill("KILL", -pid)
        Process.waitpid(pid)
      rescue Errno::ESRCH, Errno::ECHILD
        nil
      end

      def python_path
        configured = ENV[PYTHON_ENV]
        return configured if configured.present?

        venv_python = File.join(::DiscoursePdfSanitizer::Engine.root, ".venv", "bin", "python3")
        File.executable?(venv_python) ? venv_python : "python3"
      end

      def script_path
        File.join(::DiscoursePdfSanitizer::Engine.root, "script", "sanitize_pdf.py")
      end

      def read_log(file)
        file.rewind
        file
          .read(LOG_LIMIT_BYTES)
          .to_s
          .encode("UTF-8", invalid: :replace, undef: :replace, replace: "?")
          .gsub(/[[:cntrl:]&&[^\n\t]]/, "?")
      end
    end
  end
end
