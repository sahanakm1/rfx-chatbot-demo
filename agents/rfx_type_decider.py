def decide_rfx_type(user_input):
    user_input = user_input.lower()
    if "rfi" in user_input:
        return "RFI selected - used for information gathering."
    elif "rfq" in user_input:
        return "RFQ selected - used for requesting pricing."
    elif "rfp" in user_input:
        return "RFP selected - used for detailed proposals."
    else:
        return "I couldn't understand the RFx type. Please reply with RFI, RFQ, or RFP."