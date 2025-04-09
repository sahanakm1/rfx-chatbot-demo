# RFx AI Builder Assistant

This is a chatbot application designed to assist in generating RFx (Request for Information, Request for Proposal, Request for Quotation) documents based on user inputs. It integrates multiple components for document summarization, draft generation, and decision-making on RFx types.

## Features

- **Product Category Identification**: Identifies the category of the product to generate RFx documents.
- **RFx Type Selection**: Allows the user to specify the type of RFx document required (RFI, RFQ, RFP).
- **Document Summarization**: Summarizes previous documents/templates for better RFx generation.
- **Draft Generation**: Generates RFx drafts in Word format based on user inputs.
- **Easy Interface**: Interactive chatbot interface for seamless user experience.

## Installation
Prerequisites

- Python 3.12.x
- `pip` for package management
- Install Visual Studio code

To run this project locally, follow these steps:  (Please clone the Development branch and not Main branch)

```bash
git clone https://github.com/sahanakm1/rfx-chatbot-demo.git
cd rfx-chatbot-demo

### **Create a Virtual Environment**

python -m venv venv
.\venv\Scripts\activate  (venv/Scripts/activate)


### Install Dependencies

pip install -r requirements.txt

### Run the Application

Streamlit run chatbot_app.py

**Steps to Contribute:**

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -m 'Add feature').
Push to your fork (git push origin feature-branch).
Create a pull request.
