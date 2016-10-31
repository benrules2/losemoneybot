import urllib.request as ulib
import base64
import uuid
import json

def get_balance(base_url, username, password):
    url = base_url + "/v1/client/balance"
    b64str = base64.b64encode("{}:{}".format(username,password).encode('utf-8'))
    headers = {'Content-length' : '0',
               'Content-type' : 'application/json',
               'Authorization' : "Basic " + b64str.decode('utf-8')}

    req = ulib.Request(url, headers=headers)
    responseData = ulib.urlopen(req).read()
    balance = json.loads(responseData.decode('utf-8'))
    return balance

def get_sport_odds(base_url, username, password, sport = '15'):
    url = base_url + '/v1/odds?sportId=' + str(sport) + '&oddsFormat=DECIMAL'
    b64str = base64.b64encode("{}:{}".format(username,password).encode('utf-8'))
    headers = {'Content-length' : '0',
               'Content-type' : 'application/json',
               'Authorization' : "Basic " + b64str.decode('utf-8')
               }

    req = ulib.Request(url, headers=headers)
    responseData = ulib.urlopen(req).read()
    odds = json.loads(responseData.decode('utf-8'))
    return odds

def find_bet(all_odds):
    bet_info = {}
    favourable_odds = 1.91
    bet_info['sportId'] = all_odds['sportId']
    for i in all_odds['leagues']:
        bet_info['leagueId'] = i['id']
        for j in i['events']:
            bet_info['eventId'] = j['id']
            for k in j['periods']:
                bet_info['period'] = k['number']
                for l in k['moneyline'].keys():
                    odds = float(k['moneyline'][l])
                    if odds < favourable_odds and l == 'home':
                        bet_info['team'] = l
                        bet_info['lineId'] = k['lineId']
                        return bet_info

def get_bet_info(base_url, username, password, bet, favourable_odds = 1.91):

    b64str = base64.b64encode("{}:{}".format(username,password).encode('utf-8'))
    headers = {'Content-length' : '0',
               'Content-type' : 'application/json',
               'Authorization' : "Basic " + b64str.decode('utf-8')}
    url_without_team = base_url + "/v1/line?sportId={0}&leagueId={1}&eventId={2}&periodNumber={3}&betType=MONEYLINE&OddsFormat=DECIMAL"\
            .format(bet['sportId'], bet['leagueId'], bet['eventId'],bet['period'])

    url = url_without_team + "&Team=Team1"
    req = ulib.Request(url, headers=headers)
    responseData = ulib.urlopen(req).read()
    line_info = json.loads(responseData.decode('utf-8'))
        
    if line_info['price'] < favourable_odds:
        bet['minRiskStake'] = line_info['minRiskStake']            
        bet['team'] = "Team1"
        return

    url = url_without_team + "&Team=Team2"
    req = ulib.Request(url, headers=headers)
    responseData = ulib.urlopen(req).read()
    line_info = json.loads(responseData.decode('utf-8'))
    bet['minRiskStake'] = line_info['minRiskStake']            
    bet['team'] = "Team2"

def place_bet(base_url, username, password, bet, stake):
    
    url = base_url + "/v1/bets/place"
    b64str = base64.b64encode("{}:{}".format(username,password).encode('utf-8'))
    headers = {'Content-length' : '1',
               'Content-type' : 'application/json',
               'Authorization' : "Basic " + b64str.decode('utf-8')}

    data = {
            "uniqueRequestId":uuid.uuid4().hex,
            "acceptBetterLine": str(True),
            "stake": str(float(stake)),
            "winRiskStake":"RISK",
            "sportId":str(int(bet['sportId'])),
            "eventId":str(int(bet['eventId'])),            
            "lineId":str(int(bet['lineId'])),
            "periodNumber":str(int(bet['period'])),
            "betType":"MONEYLINE",
            "team":bet['team'],
            "oddsFormat":"DECIMAL"
    }

    req = ulib.Request(url, headers = headers)
    response = ulib.urlopen(req, json.dumps(data).encode("utf-8")).read().decode()
    response = json.loads(response)
    print("Bet status: " + response["status"])

if __name__ == "__main__":
    base_url = "https://api.pinnaclesports.com"
    username = '<username>'
    password = '<password>'

    stake = 1.5

    balance = get_balance(base_url, username, password)
    odds = get_sport_odds(base_url, username, password)
    bet = find_bet(odds)

    if len(bet) > 0:
        get_bet_info(base_url, username, password, bet)
    else:
        print("No bets matching criteria")

    if stake >= bet['minRiskStake'] and stake < balance['availableBalance']:
        place_bet(base_url, username, password, bet, stake)
    else:
        print("Stake too small, or not enough funds")