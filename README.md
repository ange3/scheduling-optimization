# scheduling-optimization
Implementation of a scheduling algorithm for job requests. This algorithm takes domain specific inputs (set of requests, list of available resources, and prioritized performance objectives) and returns a schedule that maximizes customer utility.

##Motivation
In this increasingly complex world, more and more industries are recognizing the importance of efficient process and task scheduling. Applications can be found in the manufacturing industry (construction of parts through batch processing), the services industry (delivery scheduling through route optimization), and even in the technology infrastructure industry (improving network speed through server time allocation). Deciding when to assign a task given a set of job requests requires optimization of multiple factors, including attributes unique to each job as well as factors dependent on other sections of the workflow. This experiment focuses on solving the “service-request” scheduling problem in the Kitchen Services Industry, where a “service-request” is defined as a customer request or a job that needs to be completed in a finite period of time. The goal of this study is to create a scheduling algorithm that takes domain specific inputs (set of service-requests, list of available resources, and prioritized performance objectives) and returns a schedule that maximizes for customer utility. Multiple methods were tested in this analysis and, ultimately, it was found that an optimization algorithm was the best method to solve this problem.

##Optimization Algorithm
I implemented an optimization algorithm to create a service schedule using data on service requests from a kitchen servicing company. For a given set of service requests, we produce a schedule that maximizes customer utility based on a pre-determined objective function. This mimics the scheduling process performed by the human scheduler but creates a series of possible schedules and chooses the most ‘ideal’ schedule. 

##Objective Function
The objective function is a linear function with weights. Each variable represents a job assignment assigned to a specific day, with coefficients that represent the utilities for each job-day pairing. The optimization algorithm solves for the optimal weighting to determine the ideal schedule.
The IBM Cplex library was used to solve the optimization problem.

##Conclusion
The optimization algorithm provides a decent solution as it considers multiple potential schedules and has flexibility, allowing more factors and constraints to be added to the model in the future. However, to ensure the feasibility of the optimization algorithm, steps must be taken to address the increase in time complexity with the increase of potential scheduling days. 
One extension of this problem looks at adding a third component to the matching algorithm, which matches a job not only to a date but also to a specific crew. This would add an extra variable to the objective function and require new constraints, such as ensuring that the chosen crew is able to accomplish a specific service request. Additional complexity can also be added by considering different groupings of crew members, instead of just assuming that crews are pre-determined.

