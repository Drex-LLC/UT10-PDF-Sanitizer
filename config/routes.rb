# frozen_string_literal: true

DiscoursePdfSanitizer::Engine.routes.draw do
  get "/examples" => "examples#index"
  # define routes here
end

Discourse::Application.routes.draw { mount ::DiscoursePdfSanitizer::Engine, at: "discourse-pdf-sanitizer" }
