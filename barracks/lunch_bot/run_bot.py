import os

from util import get_canned_header, get_logger, get_default_root_logger, get_path
from bot import Recommender, responses, DataLoader
from flask import request, Response, Flask
from slackclient import SlackClient

app = Flask(__name__)
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
MY_BOT_IS_CALLED = "lunch-bot"


def return_help(user):
    return {
        "text": "Hello @{0}! Lunch-bot did not understand you. lunch-bot accepts the following requests:"
            .format(user),
        "attachments": [
            {"text": "Returns your ratings for a restaurant: lunch-bot ratings <restaurant_name>"},
            {"text": "Returns optimal lunch groups: lunch-bot find optimal groups"},
            {
                "text": "Returns suggestions for a group (includes requesting user): "
                        "lunch-bot find restaurant @user1 @user2 ..."
            }
        ]
    }


def parse_message(msg, user):

    bits = msg.split(' ')
    if len(bits) < 2:
        out = return_help(user)

    # Assume: lunch-bot rating <restaurant_name>
    elif bits[1] == "ratings":
        out = responses("get_rating", recommender=rm, user=user, restaurant=' '.join(bits[2:]))

    # Assume: lunch-bot find optimal groups
    elif bits[1] == "find" and bits[2] == "optimal":
        out = responses("find_optimal_groups", recommender=rm)

    # Assume: lunch-bot find restaurant @user1 @user2 @user3
    elif bits[1] == "find" and bits[2] == "restaurant":
        users = [x.strip('@') for x in bits[3:]]
        users.append(user)
        out = responses("find_optimal_restaurant", recommender=rm, users=users)

    else:
        out = return_help(user)

    return out


def fail(exception, user):
    return{
        "text": "Sorry, @{user}. lucnh-bot could not understand your request. It failed because {ex}"
            .format(user=user, ex=exception)
    }


@app.route("/slack-bot", methods=["POST"])
def router():

    _logger = get_logger(__name__)
    if request.form.get("token") == os.environ.get("SLACK_WEBHOOK_SECRET"):

        # Get info from incoming request
        channel_id = request.form.get("channel_id")
        user = request.form.get("user_name")
        message = request.form.get("text")
        _logger.info("Incoming message from {0} on {1}: {2}".format(channel_id, user, message))

        # Parse and route
        try:
            response = parse_message(message, user)
        except Exception as e:
            response = fail(e, user)
        slack_client = SlackClient(os.environ.get("SLACK_TOKEN"))
        slack_client.api_call(
            "chat.postMessage",
            channel=channel_id,
            username='lunch-bot',
            icon_emoji=':sausage:',
            **response
        )

    return Response(), 200


@app.route("/model/train", methods=["POST"])
def retrain_model():
    pass


@app.route("/", methods=["GET"])
def welcome():
    return Response("Welcome to LunchBot! All your lunch are belong to us!"), 200


if __name__ == '__main__':

    loc = get_path(__file__) + '{0}'
    logger = get_default_root_logger(filename=loc.format('log/log.log'))
    get_canned_header(logger, 'LunchBot: Making Lunch Great Again!!!')

    rm = Recommender()

    logger.info("Attempting to load pre-trained model")
    model_location = loc.format('assets/model.pkl')
    data_location = loc.format("assets/data.csv")
    if os.path.isfile(model_location):
        logger.info("Found pre-trained model at {}".format(model_location))
        rm.load_pre_trained_model(loc.format('assets/model.pkl'))
    elif os.path.isfile(data_location):
        logger.info("No trained model found, attempting to build model now...")
        logger.info("Attempting to load data from {}".format(data_location))

        data = DataLoader.from_filepath(data_location)
        rm.load(data)
        rm.train()
    else:
        logger.info("No data found. Loading from Google Sheets.")
        data = DataLoader.from_google_sheet(os.getenv('LUNCH_SHEET_ID'))
        rm.load(data)
        rm.train()

    logger.info("Running app...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
