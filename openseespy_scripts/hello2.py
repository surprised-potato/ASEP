# Script content scraped from: https://openseespydoc.readthedocs.io/en/latest/src/hello2.html

mpiexec -np 4 python hello2.py

Random:
Hello from 2
Hello from 1
Hello from 3

Ordered:
Hello from 1
Hello from 2
Hello from 3

Broadcasting:
Hello from 0
Hello from 0
Hello from 0
Process 3 Terminating
Process 2 Terminating
Process 1 Terminating
Process 0 Terminating

import openseespy.opensees as ops
pid = ops.getPID()
np = ops.getNP()
# datatype = 'float'
# datatype = 'int'
datatype = 'str'
if pid == 0:
   print('Random: ')
   for i in range(1, np):
       data = ops.recv('-pid', 'ANY')
       print(data)
else:
   if datatype == 'str':
       ops.send('-pid', 0, 'Hello from {}'.format(pid))
   elif datatype == 'float':
       ops.send('-pid', 0, float(pid))
   elif datatype == 'int':
       ops.send('-pid', 0, int(pid))
ops.barrier()
if pid == 0:
   print('\nOrdered: ')
   for i in range(1, np):
       data = ops.recv('-pid', i)
       print(data)
else:
   if datatype == 'str':
       ops.send('-pid', 0, 'Hello from {}'.format(pid))
   elif datatype == 'float':
       ops.send('-pid', 0, float(pid))
   elif datatype == 'int':
       ops.send('-pid', 0, int(pid))
ops.barrier()
if pid == 0:
   print('\nBroadcasting: ')
   if datatype == 'str':
       ops.Bcast('Hello from {}'.format(pid))
   elif datatype == 'float':
       ops.Bcast(float(pid))
   elif datatype == 'int':
       ops.Bcast(int(pid))
else:
   data = ops.Bcast()
   print(data)