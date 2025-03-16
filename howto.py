from finances import app, onlinebanking, state

onlinebanking.get_client()
account = state.fintsclient.get_sepa_accounts()[2]
transactions = onlinebanking.invoke(
    methodname="get_transactions", account=account
)
print(transactions)
