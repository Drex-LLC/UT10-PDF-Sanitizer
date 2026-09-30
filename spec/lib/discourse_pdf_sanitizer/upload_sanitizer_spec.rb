# frozen_string_literal: true

RSpec.describe DiscoursePdfSanitizer::UploadSanitizer do
  before { enable_current_plugin }

  describe ".sanitize!" do
    it "replaces the input with validated sanitizer output" do
      input = Tempfile.new(%w[input .pdf])
      input.binmode
      input.write("%PDF-1.7\noriginal")
      input.flush
      runner =
        Object.new.tap do |object|
          object.define_singleton_method(:run) do |input_path:, output_path:, **_options|
            replacement_path = "#{output_path}.replacement"
            File.binwrite(replacement_path, File.binread(input_path).sub("original", "sanitized"))
            File.rename(replacement_path, output_path)
          end
        end

      described_class.sanitize!(input, runner:)

      expect(input.read).to eq("%PDF-1.7\nsanitized")
    ensure
      input&.close!
    end

    it "leaves the input unchanged when sanitization fails" do
      input = Tempfile.new(%w[input .pdf])
      input.binmode
      input.write("%PDF-1.7\noriginal")
      input.flush
      runner =
        Object.new.tap do |object|
          object.define_singleton_method(:run) do |**_options|
            raise DiscoursePdfSanitizer::SanitizationError, "failed"
          end
        end

      expect { described_class.sanitize!(input, runner:) }.to raise_error(
        DiscoursePdfSanitizer::SanitizationError,
      )
      input.rewind
      expect(input.read).to eq("%PDF-1.7\noriginal")
    ensure
      input&.close!
    end

    it "rejects input without a PDF header before invoking the sanitizer" do
      input = Tempfile.new(%w[input .pdf])
      input.write("plain text")
      input.flush

      expect { described_class.sanitize!(input) }.to raise_error(
        DiscoursePdfSanitizer::InvalidPdfError,
        "PDF header is missing",
      )
    ensure
      input&.close!
    end
  end
end
