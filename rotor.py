from ctsLS import ctsLS

A = [[0, 1, -1],[-0.075/0.4765, 0, 0],[0.075/0.035, 0, 0]]
B = [[0,0],[1/0.4765, 0],[0, 1/0.035]]
C = [[0,1,0],[0,0,1]]
D = [[0,0],[0,0]]

rotor = ctsLS(A, B, C, D)
