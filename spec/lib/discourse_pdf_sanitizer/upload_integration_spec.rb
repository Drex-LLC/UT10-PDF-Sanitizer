# frozen_string_literal: true

RSpec.describe UploadCreator, "#create_for" do
  fab!(:user)

  before do
    enable_current_plugin
    SiteSetting.authorized_extensions = "pdf"
  end

  it "rejects the upload when the sanitizer process fails" do
    python_env = DiscoursePdfSanitizer::UploadSanitizer::PYTHON_ENV
    original_python = ENV.fetch(python_env, nil)
    ENV[python_env] = "/usr/bin/false"
    input = Tempfile.new(%w[document .pdf])
    input.binmode
    input.write("%PDF-1.7\nplaceholder")
    input.flush

    upload = UploadCreator.new(input, "document.pdf").create_for(user.id)

    expect(upload).not_to be_persisted
    expect(upload.errors).to contain_exactly(
      I18n.t("discourse_pdf_sanitizer.errors.sanitization_failed"),
    )
  ensure
    original_python ? ENV[python_env] = original_python : ENV.delete(python_env)
    input&.close!
  end
end
