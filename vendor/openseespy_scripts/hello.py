# Script content scraped from: https://openseespydoc.readthedocs.io/en/latest/src/hello.html

mpiexec -np 4 python hello.py

Hello World Process: 1
Hello World Process: 2
Hello World Process: 0
Total number of processes: 4
Hello World Process: 3
Process 1 Terminating
Process 2 Terminating
Process 0 Terminating
Process 3 Terminating

import openseespy.opensees as ops
pid = ops.getPID()
np = ops.getNP()
print('Hello World Process:', pid)
if pid == 0:
   print('Total number of processes:', np)