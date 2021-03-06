import sympy
import math
import numpy
from scipy import linalg
from scipy import integrate
import matplotlib.pyplot as pylab
from mpl_toolkits.mplot3d import Axes3D

class LS:
    """ 
    Linear Systems class;
    for us this will mean discrete time systems,
    but perhaps it can be expanded to include continuous time ones as well
    """
    # this will be the complex variable throughout
    z = sympy.Symbol("z")

    def __init__(self, A, B, C, D):
        """
        for us a linear system will simply be the 4 matrices that define it
        """
        self.A = numpy.matrix(A)
        self.B = numpy.matrix(B)
        self.C = numpy.matrix(C)
        self.D = numpy.matrix(D)
        self.order = self.A.shape[0] # the order of the realization
        self.inputs = self.D.shape[1]
        self.outputs = self.D.shape[0]
        zI = LS.z*sympy.eye(self.order)
        self.G = sympy.Matrix(self.C)*(zI - sympy.Matrix(self.A)).inv()*sympy.Matrix(self.B) + sympy.Matrix(self.D)
        # TO DO: include a shape-compatibility check for A, B, C, D
        
    def __str__(self):
        """
        override of the print function
        """
        ret = ""
        ret += "A = \n" + str(self.A) + "\n"
        ret += "B = \n" + str(self.B) + "\n"
        ret += "C = \n" + str(self.C) + "\n"
        ret += "D = \n" + str(self.D)
        return ret

    

    def discretize(self, delta):
        """
        if we start off with a linear system in continuous time, then
        the sample and hold operation (as described in Hartmut's undergraduate
        course notes, chapter 7) will yield a discrete time system.
        This method implements this idea.
        delta is the sampling and hold interval
        """
        # A, C, D are all easy
        A_delta = linalg.expm(self.A * delta)
        C_delta = self.C
        D_delta = self.D
        
        # now we form the integral of e^{A \xi}
        # unfortunately neither arrays nor numpy matrices play well
        # with functions, so we will write the matrix e^{A \xi} as a list

        n = self.order
        indexes = range(n)
        exp_Ax_list = []
        
        # we will use an identity matrix
        I_n = numpy.eye(n)
        integral_e_Ax = numpy.matrix(numpy.zeros((n,n)))

        for i in indexes:
            exp_Ax_list.append([])
            e_i = numpy.matrix(I_n[:, i]) # this is a row vector
            for j in indexes:
                exp_Ax_list[i].append([])
                e_j = numpy.matrix(I_n[:, j])
                exp_Ax_list[i][j] = lambda x : float(e_i * numpy.matrix(linalg.expm(self.A * x)) * e_j.T)

        # now we are ready to integrate our array of functions
        for i in indexes:
            for j in indexes:
                tmp = integrate.quad(exp_Ax_list[i][j], 0, delta)[0]
                print "self.A = " + str(self.A)
                integral_e_Ax[i, j] = tmp
                print "self.A = " + str(self.A)
                # integrate.quad returns an array:
                # first element is the actual integral
                # second element is the error estimate
        B_delta = integral_e_Ax * self.B
        return LS(A_delta, B_delta, C_delta, D_delta)

    def plotSG(self):
        """
        for now this is only implemented for SISO systems;
        draws the set of stabilizing gains
        """
        # N is the number of points we will take on the complex unit circle
        N = 100
        if self.outputs != 1 or self.inputs != 1:
            print "the system is not SISO!"
            return 0
        h = math.pi * 2 / N
        theta = numpy.arange(0, math.pi * 2 + h, h)
        x = numpy.cos(theta)
        y = numpy.sin(theta)
        G = self.G[0] # as we do not want a matrix, just a poly
        F = 1/G
        points = []
        print F
        for i in range(N+1):
            p = complex(F.subs(LS.z, x[i] + 1j*y[i]))
            points.append(p)
        print points
        # now let us get the x and y coordinates of what we will plot
        points_x = []
        points_y = []
        for p in points:
            points_x.append(p.real)
            points_y.append(p.imag)
        # now we actually plot everything
        pylab.plot(points_x, points_y, color='red', lw=2)
        # and we add a point which we know is in the good region
        pylab.annotate(r'$\mathbb{S}(G)$', xy=(F.subs(LS.z, 0), 0))
        pylab.axis('equal')
        pylab.show()
    
    def soln(self, x0, u):
        """
        returns the solutions (x, y, u) of the given state space system
        when the initial value is x0 and u is the prescribed input.
        the vectors x0 and u_i should be written as arrays;
        this method returns an array of three sympy.Matrix objects
        """
        x_cur = numpy.matrix(x0).T 
        # as we will pass row vectors as colomn vectors for ease of use
        retx = [x_cur]
        rety = []
        retu = []
        for u_i in u:
            u_cur = numpy.matrix(u_i).T
            # same comment as for x_cur
            retu.append(u_cur)
            y_cur = self.C * x_cur + self.D * u_cur
            rety.append(y_cur)
            x_cur = self.A * x_cur + self.B * u_cur
            retx.append(x_cur)
        # now we discard the last value of retx to get arrays of the
        # same length
        retx.pop()
        return [retx, rety, retu]

    def plot_soln(self, x0, u):
        """
        this will plot those of x, y, z that have dimension at most 2
        TODO: replace "at most 2" with "at most 3"
        those that do not, will have an additional graph on which their
        norms are plotted
        """
        sol = self.soln(x0, u)
        sol_x = sol[0]
        sol_y = sol[1]
        sol_u = sol[2]
        fig = pylab.figure()
        LS.plot_single(sol_y, self.outputs, 'y', 'red', 221 ,fig)
        LS.plot_single(sol_u, self.inputs, 'u', 'yellow', 222 ,fig)
        LS.plot_single(sol_x, self.order, 'x', 'blue', 212 ,fig)
        pylab.show()
        
    @staticmethod
    def plot_single(arr, dim, name, col, placement, fig):
        if dim == 1:
            cur_plot = fig.add_subplot(placement)
            time_axis = range(len(arr))
            cur_plot.set_xlabel("Time")
            vals = []
            for a in arr:
                vals.append(float(a[0]))
            cur_plot.plot(time_axis, vals, color=col, linewidth=2, label=name, ls = '-')
            cur_plot.legend()
        elif dim == 2:
            cur_plot = fig.add_subplot(placement)
            cur_plot.axis('equal')
            x = []
            y = []
            for a in arr:
                x.append(float(a[0]))
                y.append(float(a[1]))
            cur_plot.plot(x,y,color=col, linewidth=2, label=name, ls='-')
            cur_plot.annotate(name+'(0)', xy=(x[0], y[0]))
            cur_plot.annotate(name+'(' +str(len(arr))+')', xy=(x[-1], y[-1]))
            cur_plot.legend()
        elif dim == 3:
            cur_plot = fig.add_subplot(placement, projection='3d')
            cur_plot.axis('equal')
            x = []
            y = []
            z = []
            for a in arr:
                x.append(float(a[0]))
                y.append(float(a[1]))
                z.append(float(a[2]))
            cur_plot.plot(x,y,z, color=col, linewidth=2, label=name, ls='-')
            cur_plot.legend()
        else:
            print "the screen is too flat for anything of dimension more than 3 :("

    def plot_absolute_values(self, x0, u):
        """
        this will plot the absolute values of
        x - in blue
        y - in red
        u - in yellow
        """
        solns = self.soln(x0, u)
        norm_x = []
        norm_y = []
        norm_u = []
        for val in solns[0]:
            norm_x.append(float(val.norm()))
        for val in solns[1]:
            norm_y.append(float(val.norm()))
        for val in solns[2]:
            norm_u.append(float(val.norm()))
        time_axis = range(len(solns[1]))
        pylab.title('Plot of absolute values of x, y, u')
        pylab.xlabel('Time')
        pylab.ylabel('Absolute value')
        pylab.plot(time_axis, norm_x, color='blue', linewidth=2, label='x', ls = '-')
        pylab.plot(time_axis, norm_y, color='red', linewidth=2, label='y', ls = ':')
        pylab.plot(time_axis, norm_u, color='yellow', linewidth=2, label='u', ls = '-.')
        pylab.legend()
        pylab.show()

class LureSystem(LS):
    """
    The name of the class should be pretty self explanatory;
    """
    def __init__(self, A, B, C, D, f):
        LS.__init__(self, A, B, C, D)
        self.f = f

    def __str__(self):
        ret = LS.__str__(self)
        ret += '\n'
        ret += str(self.f)
        return ret
        
    def soln(self, x0, d):
        """
        returns the solutions (x, d) of the given state space system
        when the initial value is x0 and d is the prescribed disturbance.
        the vectors x0 and d_i should be written as arrays;
        this method returns an array of two sympy.Matrix objects
        At the moment, it only allows this calculation if D = 0
        """
        if self.G - self.D != self.G:
            print "D is not equal to 0! We cannot currently deal with this."
            return 0
        x_cur = numpy.matrix(x0).T
        #as we will pass row vectors as column ones for ease of use
        retx = [x_cur]
        retd = []
        for d_i in d:
            d_cur = numpy.matrix(d_i).T # same comment as for x_cur
            retd.append(d_cur)
            x_cur = self.A * x_cur + self.B * (self.f(self.C*x_cur) + d_cur)
            retx.append(x_cur)
        # now we discard the last value of retx to get arrays of the
        # same length
        retx.pop()
        return [retx, retd]

    def plot_absolute_values(self, x0, d):
        """
        this will plot the absolute values of
        x - in blue
        d - in green
        """
        solns = self.soln(x0, d)
        norm_x = []
        norm_d = []
        for val in solns[0]:
            norm_x.append(float(val.norm()))
        for val in solns[1]:
            norm_d.append(float(val.norm()))
        time_axis = range(len(solns[1]))
        pylab.title('Plot of absolute values of x, d')
        pylab.xlabel('Time')
        pylab.ylabel('Absolute value')
        pylab.plot(time_axis, norm_x, color='blue', linewidth=2, label='x', ls = '-')
        pylab.plot(time_axis, norm_d, color='green', linewidth=2, label='d', ls = ':')
        pylab.legend()
        pylab.show()




#some examples for quick functionality checks
dsa = LS(numpy.identity(2)/2, [[2,1],[1,2]], numpy.identity(2), [[4,4],[4,4]])
asd = LS(1.0/2,3,2,1)
asd2 = LS(4,3,1,1)
asd3 = LS(2,0,0,1)
nonsquare = LS(sympy.eye(3), [[1,2],[3,4],[5,6]], [[1,2,3]], [[100, 1000]])
test_plotSG = LS([[1,0,0], [0,2,0], [0,0,3]], [[1], [1], [1]], [1,2,3], 10)
lure_test = LureSystem(2,1,1,0, lambda x: numpy.matrix(-math.log(1 + x.norm())))
lure_test2 = LureSystem(2,1,1,0, lambda x: -x/2)

def test_1dplot():
    print asd.soln(1, [1,-4,1,-1,1,-1])
    asd.plot_soln(1, [1,-4,1,-1,1,-1])

def test_2dplot():
    print dsa.soln([0,0], [[1,-1], [0,1],[1,0],[-1,1],[0,0],[1,1]])
    dsa.plot_soln([0,0], [[1,-1], [0,1],[1,0],[-1,1],[0,0],[1,1]])

def test_3dplot():
    print nonsquare.soln([0,0,0], [[-1,1],[-3,2],[3,-1],[0,0],[-5,-5]])
    nonsquare.plot_soln([0,0,0], [[-1,1],[-3,2],[3,-1],[0,0],[-5,-5]])
