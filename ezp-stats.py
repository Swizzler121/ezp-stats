#!/usr/bin/env python3
import logging #logging is used to generate a logfile
import glob, os, argparse #os is used for directory navigation, argparse for listening for cli arguments
import yaml #yaml is used to read the config file
import csv #used to open and write csv files
from string import Template #used for templating things like the log file name.
import arrow #using arrow for instead of datetime, date, timedelta
from datetime import datetime #only used to interpret arguements as it handles conversion from 1 to 2 digit months better than arrow

##### Global Variables and definitions Start #####
#open config file safely so it does not allow for code injection, assign it the variable config
with open('config.yml', "r") as f:
	config = yaml.safe_load(f)
#cwd = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-1]) #Setup Current Working Directory #deleteme maybe? not used?
#look at the config file and fetch the name and location of the diagnostic log file, spulog folder, and output log folder,
if config["flags"]["do_debug_log"] == True: #check the config file to see if logging is disabled, and disable it if this is the case
	if not config["flags"]["append_debug_log"] == True:
		logging.basicConfig(
			filename=f'{config["optional"]["debug_log"]}{arrow.now()}.log', 
			encoding='utf-8', 
			format='%(asctime)s %(levelname)-8s %(message)s',
			level=logging.DEBUG,
			datefmt='%Y-%m-%d %H:%M:%S')
	else: 
		logging.basicConfig(
			filename=f'{config["optional"]["debug_log"]}.log', 
			encoding='utf-8', 
			format='%(asctime)s %(levelname)-8s %(message)s',
			level=logging.DEBUG,
			datefmt='%Y-%m-%d %H:%M:%S')
else:
	logging.getLogger().disabled = True
try: #Log wrapper that will record any error exceptions in the log
	spufolder = config["required"]["ezproxy_spulog_folder"]
	spu = Template(config["optional"]["spulog_name_scheme"])
	outputfolder = config["optional"]["output_folder"]
	brandfolder = config["branding"]["brand_folder"]
	#TODO - look at the config spulog naming scheme and set the logfile name variable
	##### Global Variables and definitions End #####
	logging.debug(f'spu logfolder location: {spufolder}')
	#Check folder names from config and create them if they do not exist.
	if not os.path.exists(outputfolder):
		os.makedirs(outputfolder)
		logging.debug(f'Output folder created at {outputfolder}')
	#Section Listens for any CLI arguments and determines mode to start in
	logging.debug(f'Starting ArgumentParser')
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter, #lets me set the indents and returns for the help description
		#help description, the weird symbols are ANSI escape codes that change the colors of the text
		description='''\
		\033[93mPlease edit the config.yml file before running the script for the first time\033[00m

		This script analyzes EZProxy SPU logs and has multiple modes. 
		==============================================================
		\033[92m*\033[00m If no arguments are specified, it will run stats for the previous month
		\033[92m*\033[00m If only a year is specified, it will run stats for the whole year
		\033[92m*\033[00m If only a month is specified, it will run stats for that month 
		\033[92m*\033[00m If both a year and month are specified, it will run for the date specified. 

	\033[91m	Corresponding SPU log file(s) must exist in the EZProxy log folder to run stats for a time period!\033[00m
			''')
	#listen for a year argument and use lambda and strptime to determine if it is a valid year (between 0-9999)
	#parser.add_argument("-y", "--year", type=lambda d: datetime.strptime(d, '%Y'), help="specify a year")
	parser.add_argument("-y", "--year", type=lambda d: arrow.get(d, 'YYYY').format('YYYY'), help="specify a year")
	#listen for a year argument and use lamda and strptime to determine if it is a valid month (between 1-12)
	#parser.add_argument("-m","--month", type=lambda d: datetime.strptime(d, '%m'), help="specify a month (integer)")
	parser.add_argument("-m","--month", type=lambda d: arrow.get(d).format('MM'), help="specify a month (integer)")
	args = parser.parse_args()

	if (args.year and args.month):
	    logging.debug("both year and month specified")
	    #print(spu.substitute(year=args.year.strftime("%Y"), month=args.month.strftime("%m")))
	    print(spu.substitute(year=args.year, month=args.month))
	elif args.year:
		#TODO - figure out how whole-year logfile processing will work
		logging.debug("Year specified")
		loadedlogfile = spu.substitute(year=args.year, month=arrow.now().shift(months=-1).month)
		print(args.year)
		logging.debug(f'loaded the logfile {loadedlogfile}')
	elif args.month:
		logging.debug("Month specified")
		loadedlogfile = spu.substitute(year=arrow.now().shift(months=-1).year, month=args.month.strftime("%m")) #calculates the day, then uses timedelta to move to the last day of the previous month, then I use a string index to specify just the current year minus a month, and append the month from the argument
		logging.debug(f'loaded the logfile {loadedlogfile}')
	else:
		logging.debug("No arguments specified")
		#loadedlogfile = spu.substitute(year=str(datetime.today().replace(day=1) - timedelta(days=1))[0:4], month=str(datetime.today().replace(day=1) - timedelta(days=1))[5:7])#calculates the day, then uses timedelta to move to the last day of the previous month, then I use a string index to specify just the year and month out of the timecode and seperate them into individual template values
		loadedlogfile = spu.substitute(year=arrow.now().shift(months=-1).year, month=arrow.now().shift(months=-1).month) #uses arrow to calculate the current time, then subtract a month
		logging.debug(f'loaded the logfile {loadedlogfile}')
		outputfile = f"{config['optional']['output_file_prefix']}{arrow.now().shift(months=-1).format('YYYYMM')}"
		#outputfile = f'{config["optional"]["output_file_prefix"]}{str(datetime.today().replace(day=1) - timedelta(days=1))[0:7].replace("-","")}'
		logging.debug(f'set output file name to {outputfile}')
except Exception as e: #Sends any error exception to the log
    logging.error(e, exc_info=True)