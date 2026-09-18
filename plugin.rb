# frozen_string_literal: true

# name: discourse-pdf-sanitizer
# about: TODO
# meta_topic_id: TODO
# version: 0.0.1
# authors: Discourse
# url: TODO
# required_version: 2.7.0

enabled_site_setting :discourse_pdf_sanitizer_enabled

module ::DiscoursePdfSanitizer
  PLUGIN_NAME = "discourse-pdf-sanitizer"
end

require_relative "lib/discourse_pdf_sanitizer/engine"

after_initialize do
  # Code which should run after Rails has finished booting
end
