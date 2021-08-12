from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from helper import get_db, save_user_context
from conversation import *
import logging

app = Flask(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

context = dict()
RESTART_SESSION_INDICATOR = 0

@app.route("/bot", methods=["POST"])
def bot():
    incoming_message = request.values
    user = incoming_message["From"]

    db = get_db(logger)
    user_context = db.get(user, None)
    logger.info("Got user context for user {}: {}".format(user, user_context))
    if not user_context: 
        user_context = {"next_conversation_phase": "IntroductionMessage"}
        save_user_context(user, user_context, logger)

    # check if user entered 0 to restart session
    try:
        if int(incoming_message.get("Body", "")) == RESTART_SESSION_INDICATOR:
            user_context["next_conversation_phase"] = "MainMenuMessage"
            save_user_context(user, user_context)
    except Exception:
        pass

    # initialize conversation phase object
    conversation_phase_constructor = globals()[user_context["next_conversation_phase"]]
    conversation_phase = conversation_phase_constructor(incoming_message, user_context, logger)

    # run conversation phase
    conversation_phase.execute()
    # save in case user context was updated
    save_user_context(user, conversation_phase.user_context, logger)

    resp = MessagingResponse()
    msg = resp.message()

    msg.body(conversation_phase.text)
    return str(resp)

if __name__ == "__main__":
    app.run()
