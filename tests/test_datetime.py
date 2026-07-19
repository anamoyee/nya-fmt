import datetime as dt

td_neg1d = dt.timedelta(days=-1)
td_neg1m = dt.timedelta(minutes=-1)

TZ = dt.datetime.now().astimezone().tzinfo


def test_date(π):
	π["date.today()                -> "] = dt.date.today()  # ruff:ignore[call-date-today]
	π["datetime.now(tz=).date()    -> "] = dt.datetime.now(tz=TZ).date()
	print()
	π["date.today()            -1d -> "] = dt.date.today() + td_neg1d  # ruff:ignore[call-date-today]
	π["datetime.now(tz=).date()-1d -> "] = dt.datetime.now(tz=TZ).date() + td_neg1d


def test_time(π):
	π["datetime.now(tz=).time()    -> "] = dt.datetime.now(tz=TZ).time()
	print()
	π["datetime.now(tz=).time()-1m -> "] = (dt.datetime.now(tz=TZ) + td_neg1m).time()


def test_datetime(π):
	π["datetime.now       -> "] = dt.datetime.now()  # ruff:ignore[call-datetime-now-without-tzinfo]
	π["datetime.now+tz    -> "] = dt.datetime.now(tz=TZ)
	print()
	π["datetime.now   -1m -> "] = dt.datetime.now() + td_neg1m  # ruff:ignore[call-datetime-now-without-tzinfo]
	π["datetime.now+tz-1m -> "] = dt.datetime.now(tz=TZ) + td_neg1m
