# frozen_string_literal: true

# name: discourse-pdf-sanitizer
# about: Sanitizes PDF attachments before Discourse stores them
# version: 0.1.0
# authors: L360
# url: https://github.com/diederichL360C/UT10-Upload-Sanitizer
# required_version: 2.7.0

enabled_site_setting :discourse_pdf_sanitizer_enabled

module ::DiscoursePdfSanitizer
  PLUGIN_NAME = "discourse-pdf-sanitizer"
end

require_relative "lib/discourse_pdf_sanitizer/engine"

after_initialize do
  require_relative "lib/discourse_pdf_sanitizer/upload_sanitizer"
  require_relative "lib/discourse_pdf_sanitizer/uploads_controller_extension"

  reloadable_patch do
    ::UploadsController.prepend(::DiscoursePdfSanitizer::UploadsControllerExtension)
  end

  on(:before_upload_creation) do |file, _is_image, upload, _validate|
    next unless upload.original_filename&.match?(/\.pdf\z/i)

    begin
      ::DiscoursePdfSanitizer::UploadSanitizer.sanitize!(file)
      upload.filesize = File.size(file.path)
    rescue StandardError => error
      Rails.logger.warn(
        "[#{::DiscoursePdfSanitizer::PLUGIN_NAME}] Rejected PDF upload: " \
          "#{error.class.name}: #{error.message}",
      )
      upload.errors.add(:base, I18n.t("discourse_pdf_sanitizer.errors.sanitization_failed"))
    end
  end
end
