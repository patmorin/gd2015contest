from __future__ import division
import re
import random


header=r'''\documentclass{article}

\usepackage{tikz}

\newcommand{\xcol}{red}
\newcommand{\ocol}{blue}
\newcommand{\ecol}{white}

\usepackage[a1paper,margin=1cm]{geometry}

\pagestyle{empty}

\begin{document}
\begin{tikzpicture}'''

footer=r'''
\end{tikzpicture}
\end{document}'''



def draw_square(pos, size, val):
    d = dict( [('-', 'white'), ('X', 'red'), ('O', 'blue')] )
    return r'\draw [black,fill={}] ({}mm,{}mm) rectangle ({}mm,{}mm);'\
          .format(d[val], pos[0], pos[1], pos[0]+size/3, pos[1]+size/3)

def draw_board(pos, size, board, winner):
    wincol = ['blue', 'purple', 'red', 'green'][winner+1]
    pos = pos[0]-size/2, pos[1]-size/2
    s = ''
    #s = r'\draw [{},fill={}] ({}mm,{}mm) rectangle ({}mm,{}mm);'\
    #    .format(wincol, wincol, pos[0]-size/4, pos[1]-size/4, pos[0]+1.25*size, 
    #            pos[1]+1.25*size)  
    for i in range(9):
        s += draw_square( ( pos[0]+(i%3)*(size/3), pos[1]+(i//3)*(size/3) ),
                          size, board[i]);
    return s + '\n'

class vertex(object):
    def __init__(self, label):
        self.label = label
        self.neighbours = []
        self.xy = (0, 0)
        self.winner = None

    def moves(self):
        return sum([c != '-' for c in self.label])

def read_graph(filename):
    lines = open(filename).read().splitlines()
    n, m = 765, 2096

    # Read vertices.
    vertices = []
    for i in range(n):
        vertices.append(vertex(lines[i]))
        vertices[i].orig_index = i

    # Sort vertex list by number of moves.
    vertices = sorted(vertices, key=lambda u: u.moves())
    vertex_map = [-1]*n
    for i in range(n):
        vertex_map[vertices[i].orig_index] = i

    # Read edges.
    for i in range(m):
        m = re.match(r'\((\d+),(\d+)\)', lines[n+i])
        u, w = vertex_map[int(m.group(1))-1], vertex_map[int(m.group(2))-1]
        if u > w: u, w = w, u
        vertices[u].neighbours.append(w)

    # Setup parent pointers
    for u in vertices:
        u.parents = []
    for u in vertices:
        for w in [vertices[j] for j in u.neighbours]:
            w.parents.append(u)

    return vertices


def check_x_win(label):
    """Test if X is a winner on the given board label"""
    patterns = [(0,1,2), (3,4,5), (6,7,8), (0,3,6),
                (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for p in patterns:
        if label[p[0]] == 'X' and label[p[1]] == 'X' and label[p[2]] == 'X':
            return 1
    return 0


def minimax(vertices):
    """Determine the value of the game for each vertex in the graph.

    The values of the game is -1 if O wins, 0 for a draw, and +1 if X wins
    """
    for i in reversed(range(len(vertices))):
        u = vertices[i]
        if u.moves() == 9: # Board is full
            u.winner = check_x_win(u.label)
        elif u.moves() % 2 == 0:  # X is playing, maximizer
            u.winner = max([-1] + [vertices[j].winner for j in u.neighbours])
        else:              # Y is playing, minimizer.
            u.winner = min([1] + [vertices[j].winner for j in u.neighbours])


def draw_path(points, options):
    t = ["({}mm,{}mm)".format(p[0],p[1]) for p in points]
    return r'\draw [{}]'.format(options) + "--".join(t) + ';';

if __name__ == "__main__":
    """Program entry point."""
    # Page size, in millimetres.
    width, height = 564, 821

    # Print LaTeX preamble.
    print header

    # Read the input graph.
    vertices = read_graph('tictactoe.txt')

    # Determine the winner for each node -1=O, 0=draw, 1=X.
    minimax(vertices)

    # These are the fractions of width devoted to O, draw, and X.
    fractions = [2/5, 1/5, 2/5]

    for m in range(10):
        layer = [w for w in vertices if w.moves() == m]
        for winner in [-1, 0, 1]:
            winlayer = [w for w in layer if w.winner == winner]
            if len(winlayer) == 0: continue
            for w in winlayer:
                parents = [p for p in w.parents if p.winner == winner]
                if len(w.neighbours) == 0:
                    w.sortkey = [-2**20,None,2**20][winner+1] # FIXME.
                elif parents:
                    w.sortkey = sum([p.xy[0] for p in parents])/len(parents)
                else:
                    w.sortkey = [2**20,width/2,-2**20][winner+1] # FIXME.
            winlayer = sorted(winlayer, key=lambda u: u.sortkey)

            mywidth = width*fractions[winner+1]
            deltax = mywidth/(len(winlayer)+1)
            xblock = deltax + width*sum(fractions[:winner+1])
            size = min(40, mywidth/(1.5*len(winlayer)))
            for u in winlayer:
                u.size = size
                u.xy = (xblock, (10-m)*height/11)
                xblock += deltax

    # Draw backgrounds.
    for i in [0, 1, 2]:
        col = ['cyan', 'white', 'pink'][i]
        print r'\draw [{},fill={}] ({}mm,{}mm) rectangle ({}mm,{}mm);'\
              .format(col, col, width*sum(fractions[:i]), 0, width, height)
        
    # Draw the boring edges.
    for m in range(9):
        layer = [u for u in vertices if u.moves() == m]
        for u in layer:
            nbs = [vertices[j] for j in u.neighbours 
                        if vertices[j].winner != u.winner]
            q = len(nbs)   
            if q == 0: continue
            xdelta = u.size/(q+1)
            xblock = u.xy[0]-u.size/2
            for w in nbs:
                midy = random.uniform(u.xy[1]-20, w.xy[1]+20)
                print draw_path([ (u.xy[0], u.xy[1]-u.size/2),
                                  (xblock, midy),
                                  (w.xy[0], midy),
                                  (w.xy[0], w.xy[1]+w.size/2) ], 'lightgray, rounded corners' )
                xblock += xdelta
                    
    """for u in vertices:
        for w in [vertices[i] for i in u.neighbours]:
            if u.winner != w.winner:
                print r'\draw [{}] ({}mm,{}mm)--({}mm,{}mm);'\
                    .format('lightgray', u.xy[0], u.xy[1]-u.size/2, 
                            w.xy[0], w.xy[1]+w.size/2);"""
    # Draw the core edges.
    for u in vertices:
        for w in [vertices[i] for i in u.neighbours]:
            if u.winner == w.winner:
                print r'\draw [{}] ({}mm,{}mm)--({}mm,{}mm);'\
                    .format('black', u.xy[0], u.xy[1]-u.size/2, 
                            w.xy[0], w.xy[1]+w.size/2);

    # Draw the vertices.
    for u in vertices:
        print draw_board(u.xy, u.size, u.label, u.winner)


    print footer




