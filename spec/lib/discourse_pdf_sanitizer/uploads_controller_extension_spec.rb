# frozen_string_literal: true

RSpec.describe DiscoursePdfSanitizer::UploadsControllerExtension do
  before do
    enable_current_plugin
    SiteSetting.discourse_pdf_sanitizer_enabled = true
  end

  let(:controller_class) do
    Class.new do
      def validate_before_create_direct_upload(**)
      end

      def validate_before_create_multipart(**)
      end

      prepend DiscoursePdfSanitizer::UploadsControllerExtension
    end
  end

  it "rejects direct and multipart PDFs that Discourse cannot download for sanitization" do
    controller = controller_class.new
    arguments = {
      file_name: "document.PDF",
      file_size: ExternalUploadManager::DOWNLOAD_LIMIT,
      upload_type: "composer",
    }

    expect { controller.send(:validate_before_create_direct_upload, **arguments) }.to raise_error(
      ExternalUploadHelpers::ExternalUploadValidationError,
    )
    expect { controller.send(:validate_before_create_multipart, **arguments) }.to raise_error(
      ExternalUploadHelpers::ExternalUploadValidationError,
    )
  end

  it "allows PDFs small enough to pass through the sanitizer" do
    controller = controller_class.new
    arguments = {
      file_name: "document.pdf",
      file_size: ExternalUploadManager::DOWNLOAD_LIMIT - 1,
      upload_type: "composer",
    }

    expect {
      controller.send(:validate_before_create_direct_upload, **arguments)
    }.not_to raise_error
  end

  it "does not affect other file types" do
    controller = controller_class.new
    arguments = {
      file_name: "archive.zip",
      file_size: ExternalUploadManager::DOWNLOAD_LIMIT,
      upload_type: "composer",
    }

    expect {
      controller.send(:validate_before_create_direct_upload, **arguments)
    }.not_to raise_error
  end
end
