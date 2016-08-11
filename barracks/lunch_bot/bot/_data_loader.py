import pandas as pd
import os
from util import get_logger


class DataLoader(object):

    def __init__(self):
        self.logger = get_logger(__name__)

    @classmethod
    def from_filepath(cls, filepath):
        dl = DataLoader()
        dl.filepath = filepath

        dl._load_file()
        return dl

    @classmethod
    def from_google_sheet(cls, sheet_id):
        dl = DataLoader()
        dl.sheet_id = sheet_id

        dl._load_google_sheet()

        return dl

    def _load_google_sheet(self):
        from oauth2client.service_account import ServiceAccountCredentials
        from oauth2client import crypt, GOOGLE_REVOKE_URI
        import gspread

        pvt_key = os.getenv('PRIVATE_KEY', '')
        pvt_key = pvt_key.replace('\\n', '\n')

        config = dict(service_account_email=os.getenv('CLIENT_EMAIL'),
                      signer=crypt.Signer.from_string(pvt_key),
                      scopes=['https://spreadsheets.google.com/feeds'],
                      private_key_id=os.getenv('PRIVATE_KEY_ID'),
                      client_id=os.getenv('CLIENT_ID'),
                      token_uri=os.getenv('TOKEN_URI'),
                      revoke_uri=GOOGLE_REVOKE_URI,
                      )
        credentials = ServiceAccountCredentials(**config)

        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(self.sheet_id).sheet1
        records = sheet.get_all_records(head=6)

        df = pd.DataFrame.from_dict(records)
        df.set_index('Restaurant', inplace=True)
        self.data = df.apply(lambda c: pd.to_numeric(c, errors='coerce'))

    def _load_file(self):
        data = pd.read_csv(self.filepath, skiprows=5)
        data.set_index('Restaurant', inplace=True)

        self.data = data

        self.logger.info('Data successfully loaded')


if __name__ == '__main__':

    dl = DataLoader('/Users/jjardel/Work/bot-army/barracks/lunch-bot/data/survey_data.csv')
