# orchestrator.py

from agents import category_identifier, rfx_type_decider, document_summarizer, draft_generator

class Orchestrator:
    def __init__(self):
        self.user_input = ""
        self.category = ""
        self.rfx_type = ""
        self.summary = ""
        self.draft = ""

    def set_user_input(self, text):
        self.user_input = text

    def ask_for_category(self):
        return category_identifier.ask_for_category()

    def set_category(self, user_category_input):
        self.category = category_identifier.identify_category(user_category_input)

    def run_rfx_decision(self):
        self.rfx_type = rfx_type_decider.decide_rfx_type(self.user_input)

    def run_document_summary(self):
        self.summary = document_summarizer.summarize_docs()

    def run_draft_generation(self):
        self.draft = draft_generator.generate_draft(
            category=self.category,
            rfx_type=self.rfx_type,
            summary=self.summary
        )

    def run_all_agents(self):
        self.run_rfx_decision()
        self.run_document_summary()
        self.run_draft_generation()