from barracks.lunch_bot.util import get_canned_header, get_default_root_logger, get_path
from barracks.lunch_bot.bot import DataLoader, Recommender
import os

# call train_bot.py if you need to train the model.
# Save the trained results to disk so run_bot.py can simply load the model.


if __name__ == '__main__':

    loc = get_path(__file__) + '{0}'
    logger = get_default_root_logger(filename=loc.format('log/log.log'))

    logger = get_canned_header(logger, 'Training LunchBot')

    dl = DataLoader.from_google_sheet(os.getenv('LUNCH_SHEET_ID'))

    # load and train recommender
    recommender = Recommender()
    recommender.load(dl.data)
    recommender.train()

    recommender.save_model(loc.format('assets/model.pkl'))
