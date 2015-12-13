from __future__ import print_function

import sys, csv, datetime
from datetime import timedelta

import cplex
from cplex.exceptions import CplexError

#CONSTANTS
DAYS = 6  #CHANGE ME!
dt_format = "%m/%d/%y"
SCHEDULE_START_DATE = datetime.datetime.strptime("05/08/15",dt_format)
DAILY_REQUESTS_LIMIT = 12
DAILY_WORK_HOUR_LIMIT = 104
DATA_SET = "may_" + str(DAYS) + "day_schedule.csv"

# GLOBAL VARIABLES
# 1) Objective Function
my_obj = []
my_ub = []
my_lb = []
my_types = []
my_colnames = []

# 2) Request Info table
request_info = {}

# 3) Gold Schedule
gold_schedule = {}

def calculateUtility(requestID, day):
  this_request = request_info[requestID]
  date_today = SCHEDULE_START_DATE+timedelta(days=day)
  date_score = (date_today-this_request["date"]).days
  
  if date_score > 14:
    date_score = 14
  urgency_score = this_request["urgency"]*10
  utility = date_score + urgency_score
  return utility

def setupLP(infoDict):
  N_SERVICE_REQUESTS = infoDict["N_SERVICE_REQUESTS"]
  M_DAYS = infoDict["M_DAYS"]
  num_vars = infoDict["num_vars"]
  for i in range(1,N_SERVICE_REQUESTS+1):
    for j in range(1,M_DAYS+1):
      my_obj.append(calculateUtility(i,j))  #add utility for x(ij)
      var_name = "x-" + repr(i) + "-" + repr(j)  #var_name = x-1-1 means x variable for request 1 on day 1
      my_colnames.append(var_name)
  my_ub = [1.0 for x in range(0,num_vars)]
  my_lb = [0.0 for x in range(0,num_vars)]
  my_types = ["I"] * num_vars  #type is integer for all variables - to access types, prob.variables.type.integer

def populatebyrow(prob, infoDict):
    N_SERVICE_REQUESTS = infoDict["N_SERVICE_REQUESTS"]
    M_DAYS = infoDict["M_DAYS"]
    prob.objective.set_sense(prob.objective.sense.maximize)

    prob.variables.add(obj=my_obj, ub=my_ub, lb=my_lb, names=my_colnames, types = my_types)
      # my_obj is coefficients of the objective function, ub=list of upper bound floats, lb = list of lower bound floats, names = list of string var names, types = list of single character strings specifying type of each var

    # Constraint 1: Each request can only be satisfied once (sum(xij) for all i = 1)
    c1_rows = []
    c1_rownames = []
    ones = [1.0 for x in range(0,M_DAYS)]
    for requestID in range(1,N_SERVICE_REQUESTS+1):
      this_row = []
      day_row_vars = ["x-"+repr(requestID)+"-"+repr(day) for day in range(1,M_DAYS+1)]
      this_row.append(day_row_vars)
      this_row.append(ones)
      c1_rows.append(this_row)
      c1_rownames.append("request"+repr(requestID))

    c1_rhs = [0.0 for x in range(0,N_SERVICE_REQUESTS)]
    c1_sense = "R"*N_SERVICE_REQUESTS
    c1_rangevalues = [1 for x in range(0,N_SERVICE_REQUESTS)]  # rhs[i] <= rhs[i] + range_value[i]

    prob.linear_constraints.add(lin_expr=c1_rows, senses=c1_sense,
                                rhs=c1_rhs, names=c1_rownames, range_values=c1_rangevalues)

    # Constraint 2: Daily limit on the number of service requests that can be completed (sum(xij) for all j <= DAILY_REQUESTS_LIMIT)
    c2_rows = []
    c2_rownames = []

    for day in range(1,M_DAYS+1):
      this_row = []
      request_row_vars = ["x-"+repr(requestID)+"-"+repr(day) for requestID in range(1,N_SERVICE_REQUESTS+1)]
      job_times = [request_info[x]["time"] for x in range(1,N_SERVICE_REQUESTS+1)] #get job time for each request
      this_row.append(request_row_vars)
      this_row.append(job_times)
      c2_rows.append(this_row)
      c2_rownames.append("day"+repr(day))

    c2_rhs = [0.0 for x in range(0,M_DAYS)]
    c2_sense = "R"*M_DAYS
    c2_rangevalues = [DAILY_WORK_HOUR_LIMIT for x in range(0,M_DAYS)]

    prob.linear_constraints.add(lin_expr=c2_rows, senses=c2_sense,
                                rhs=c2_rhs, names=c2_rownames, range_values=c2_rangevalues)


def lp(pop_method, infoDict):
    N_SERVICE_REQUESTS = infoDict["N_SERVICE_REQUESTS"]
    M_DAYS = infoDict["M_DAYS"]
    try:
        my_prob = cplex.Cplex()

        if pop_method == "r":
            handle = populatebyrow(my_prob, infoDict)
        else:
            raise ValueError('pop_method must be "r"')

        my_prob.solve()
    except CplexError as exc:
        print(exc)
        return

    numrows = my_prob.linear_constraints.get_num()
    numcols = my_prob.variables.get_num()

    # initialize schedule tracker
      # {Day 1: (set of request IDs), Day 2: (set of request IDs), ...}
    schedule = {}
    for i in range(1,M_DAYS+1):
      schedule[i] = set()

    print()
    # solution.get_status() returns an integer code
    print("Solution status = ", my_prob.solution.get_status(), ":", end=' ')
    # the following line prints the corresponding string
    print(my_prob.solution.status[my_prob.solution.get_status()])
    print("Solution value  = ", my_prob.solution.get_objective_value())
    slack = my_prob.solution.get_linear_slacks()
    pi = my_prob.solution.get_dual_values()
    x = my_prob.solution.get_values()
    dj = my_prob.solution.get_reduced_costs()
    names = my_prob.variables.get_names()
    num_scheduled = 0
    for j in range(numcols):
        if (x[j] == 1):
          print("Column %d:  Name = %s Value = %10f Reduced cost = %10f" %
              (j, names[j], x[j], dj[j]))
          split_vals = names[j].split("-")
          requestID = int(split_vals[1])
          day = int(split_vals[2])
          schedule[day].add(requestID)
          num_scheduled += 1

    my_prob.write("lpex1.lp")
    print("Solution Schedule")
    print(schedule)
    print("Gold Schedule")
    print(gold_schedule)


    # Print out Results
    print("** Accuracy **")
    accuracy_list = []
    for i in range(1, M_DAYS+1):
      print("Day ", i)
      intersection = schedule[i] & gold_schedule[i]
      print(intersection)
      accuracy = 0
      if len(gold_schedule[i]) != 0:
        accuracy = float(len(intersection)) / float(len(gold_schedule[i]))
      print("Accuracy = ", accuracy*100, "%")
      accuracy_list.append(accuracy)
    average_accuracy = sum(accuracy_list)/len(accuracy_list)
    print("Total Utility  = ", my_prob.solution.get_objective_value())
    print("%d requests scheduled out of %d." % (num_scheduled, N_SERVICE_REQUESTS))
    print("Percentage requests scheduled = ", float(num_scheduled)/N_SERVICE_REQUESTS*100, "%")
    print("Average Accuracy = ", average_accuracy*100, "%")
    print("Done!")

# Reads in data from given CSV file to populate request info
def readData(csvFile, infoDict):
  M_DAYS = infoDict["M_DAYS"]
  schedule_day = 0
  for i in range(1,M_DAYS+1):
    gold_schedule[i] = set()
  f = open(csvFile, 'rU')
  header = f.readline() #skip header line
  filereader = csv.reader(f)
  for row in filereader:
    if not str.isdigit(row[0]):
      schedule_day += 1
      continue
    requestID = int(row[0])
    this_request_info = {}
    this_request_info["date"] = datetime.datetime.strptime(row[1], dt_format)
    this_request_info["urgency"] = int(row[2])
    this_request_info["time"] = int(row[3])
    request_info[requestID] = this_request_info
    # add requestID to gold schedule
    gold_schedule[schedule_day].add(requestID)
  #Set global variables
  infoDict["N_SERVICE_REQUESTS"] = len(request_info)
  infoDict["num_vars"] = infoDict["N_SERVICE_REQUESTS"]*infoDict["M_DAYS"]
  print("%d requests to schedule in %d days" % (infoDict["N_SERVICE_REQUESTS"], infoDict["M_DAYS"]))

if __name__ == "__main__":
    infoDict = {"N_SERVICE_REQUESTS": 0, "M_DAYS": DAYS, "num_vars": 0}
    readData(DATA_SET, infoDict)
    setupLP(infoDict)
    lp("r", infoDict)
