# frozen_string_literal: true

module DiscoursePdfSanitizer
  module UploadsControllerExtension
    protected

    def validate_before_create_multipart(file_name:, file_size:, upload_type:)
      super
      validate_pdf_sanitizer_download_limit!(file_name, file_size)
    end

    def validate_before_create_direct_upload(file_name:, file_size:, upload_type:)
      super
      validate_pdf_sanitizer_download_limit!(file_name, file_size)
    end

    private

    def validate_pdf_sanitizer_download_limit!(file_name, file_size)
      return unless SiteSetting.discourse_pdf_sanitizer_enabled?
      return unless file_name.match?(/\.pdf\z/i)
      return if file_size < ::ExternalUploadManager::DOWNLOAD_LIMIT

      raise ::ExternalUploadHelpers::ExternalUploadValidationError,
            I18n.t("discourse_pdf_sanitizer.errors.direct_upload_too_large")
    end
  end
end
