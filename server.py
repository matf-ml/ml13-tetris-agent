import time, socket, json ,random,copy,math
from time import sleep




#weights =  [0,0,0,0,0,0,0,0]
weights =  [-1.279500 , -1.278800 ,-1.302500, -89.271100 ,-0.494500, -0.131500, -0.496600, -5.745800]
gamma = 0.95
alpha = 0.000001
explore_change=0.00



br_igara = 0
conn = None
lines_cleared=0
MAX_GAMES = 20

training=False
avg= False
play= True
deep = False


terminos = {"T" : [[[0,1,0],[1,1,1]],[[1,0],[1,1],[1,0]],[[1 ,1, 1],[0,1,0]],[[0,1],[1,1],[0,1]]],
			"J" : [[[0,0,1],[1 ,1 ,1]],[[1,1],[0,1],[0,1]],[[1,1,1],[1,0,0]],[[1,0],[1,0],[1,1]]],
			"Z" : [[[0,1,1],[1 ,1 ,0]],[[1,0],[1,1],[0,1]]],
			"O" : [[[1,1 ],[1,1]]],
			"S" : [[[1,1,0],[0 ,1 ,1]],[[0,1],[1,1],[1,0]]],
			"L" : [[[1,0,0],[1, 1 ,1]],[[0,1,],[0,1],[1,1]],[[1,1,1],[0,0,1]],[[1,1],[1,0],[1,0]]],
			"I" : [[[1 ,1 ,1,1]],[[1],[1],[1],[1]]]}
terminos_rotate = {"T" : 4,"J" : 4,"Z" : 2,"O" : 1,"S" : 2,"L" : 4,"I" : 2}
terminos_move = {"T" : [(-4,3),(-5,3),(-4,3),(-4,4)],
				 "J" : [(-4,3),(-4,4),(-4,3),(-5,3)],
				 "Z" : [(-4,3),(-5,3)],
				 "O" : [(-4,4)],
				 "S" : [(-4,3),(-5,3)],
				 "L" : [(-4,3),(-4,4),(-4,3),(-5,3)],
				 "I" : [(-3,3),(-5,4)]}


def waitForConnection():
    global conn, callbacksThread
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.bind(("127.0.0.1", 81))
    s.listen(1)
    s.setblocking(1)
    print("Waiting connection from emulator...")
    conn, addr = s.accept()
    conn.setblocking(1)
    conn.settimeout(20)
    print("Connected: ", conn)




def recvall(sock):
    BUFF_SIZE = 2048 # 2 KiB
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            break
    return data

def get_board(ram):
	board = [ [ 0 for i in range(21) ] for j in range(21) ]
	for i in range(0,len(ram[:200])):
		row = int((i / 10))
		col = int(i % 10)
		if(int(ram[i])!= 239):
			board[row][col] = 1
		else:
			board[row][col] = 0
	return board

def print_board(board):
	for i in range(0,20):
		red = ""
		for j in range(0,10):
			if(board[i][j]==1):
				red=red+"x "
			else:
				red= red  +"o "
		print(red)
	print()

def tbc(board,i):
	clear_line = True
	for j in range (0,10):
		if(board[i][j]==0):
			clear_line=False
			break;
	return clear_line

def get_parameters(board):
	global lines_cleared
	min = min_hight_board(board)
	max = max_hight_board(board)
	return [max,evenness(board),number_of_holes(board),acc_hight(board),lines_cleared,min,avg_hight_board(board),(max-min)*(max-min)]


def removed_lines(board):
	removed = 0
	for i in range(0,20):
		red = True
		for j in range(0,10):
			if(board[i][j]==0):
				red=False
				break;
		if(red):
			removed+=1
	return removed

def reward(old_params,new_params,rem):
	rew = 5 * (rem * rem) - (new_params[3] - old_params[3]) - (new_params[2] - old_params[2])*10
	return rew

def eval(board):
	global lines_cleared
	min = min_hight_board(board)
	max = max_hight_board(board)
	return weights[0]*max_hight_board(board)+weights[1]*evenness(board)+weights[2]*number_of_holes(board)+weights[3]*acc_hight(board)+lines_cleared*weights[4]+min*weights[5]+avg_hight_board(board)*weights[6]+(max-min)*(max-min)*weights[7]

def max_hight_board(board):
	max=0
	for i in range(0,10):
		tmp=max_hight(board,i)
		if(tmp>max):
			max=tmp

	return max-removed_lines(board)


def min_hight_board(board):
	min=20
	for i in range(0,10):
		tmp=max_hight(board,i)
		if(tmp<min):
			min=tmp

	return min-removed_lines(board)

def avg_hight_board(board):
	avg=0
	for i in range(0,10):
		avg+=max_hight(board,i)
		

	return avg/10

def send_move(move,t):
	rot=move[0]
	m=move[1]+terminos_move[t][rot][0]
	b=b""
	if((t=="J" or t=="L") and rot%2!=0):
		rot+=2
	for i in range(0,rot):
		b+=b"B "

	str=b""
	if(m>0):
	   str=b"right "
	if(m<0):
	   str=b"left "
	   m*=-1
	for i in range(0,m):
		b+=str
	conn.send(b)


def evenness(board):
	sum=0
	for i in range(0,9):
		sum+=abs(max_hight(board,i)-max_hight(board,i+1))
	return sum


def acc_hight(board):
	sum=0
	for i in range(0,10):
		sum+=max_hight(board,i)
	return sum-removed_lines(board)*10

def number_of_holes(board):
	holes=0
	for j in range(0,10):
		hole = False
		for i in range(0,20):
			if(board[i][j]==1 and  (not(tbc(board,i)))):
				hole = True
			if(board[i][j]==0 and hole):
				holes+=1
	return holes

def get_piece(num):
	n = int(num)
	if(n==2):
		return "T"
	if(n==7):
		return "J"
	if(n==8):
		return "Z"
	if(n==10):
		return "O"
	if(n==11):
		return "S"
	if(n==14):
		return "L"
	if(n==18):
		return "I"

def find_best_move(board,tetris_piece):
   lista_bordova=[]
   lista_evaluacija=[]
   lista_poteza = []
   for i in range(0,terminos_rotate[tetris_piece]):
       br_polozaja=terminos_move[tetris_piece][i][1]-terminos_move[tetris_piece][i][0]+1
       for j in range(0,br_polozaja):
            tmp = simulate_board(board,tetris_piece,(i,j))
            if(tmp is not None):
               #print_board(tmp)
               #print(i,j)
               eval_val = eval(tmp)
               #print(eval_val)
               lista_bordova.append(tmp)
               lista_evaluacija.append(eval_val)
               lista_poteza.append((i,j))

   if(len(lista_evaluacija)==0):
      return board,(0,0)
   max_eval = max(lista_evaluacija)
   ind=lista_evaluacija.index(max_eval)
   best_move = lista_poteza[ind]
   best_board = lista_bordova[ind]

   if random.random() < explore_change:
      rand = random.randint(0, len(lista_poteza) - 1)
      move = lista_poteza[rand]
      best_board = lista_bordova[rand]
   else:
       move = best_move
   return best_board,move

def max_hight_from_top(board,j):
	for i in(range(20)):
		if (board[i][j] ==1):
			return i
	return 19

def max_hight(board,j):
	for i in(range(20)):
		if (board[i][j] ==1):
			return 19-i+1
	return 0

def simulate_board(board,pice, move):
	board2 = copy.deepcopy(board)
	term_matrix = terminos[pice][move[0]]
	t_len = len(terminos[pice][move[0]][0])
	pocetna = max_hight_from_top(board2,move[1])
	if(pice == "Z" or pice == "S"):
		pocetna-=1
	for i in range(1,t_len):
		tmp=max_hight_from_top(board2,move[1]+i)
		if(tmp<pocetna):
			pocetna = tmp
	for i in reversed(range(0,pocetna+1)):
		board2 = copy.deepcopy(board)
		board_sim=ubaci(board2,term_matrix,i,move[1])
		if(board_sim[1]==1):
			return board_sim[0]
		if(board_sim[1]==-1):
			break;
		if(board_sim[1]==0):
			continue;
	return None


def ubaci(board,term_matrix,h,w):
	if(term_matrix[0][0]==0 or term_matrix[0][-1]==0 and len(term_matrix[0])==2):		
		h=h+1
		if(term_matrix[1][0]==0 or term_matrix[1][1]==0 and len(term_matrix[0])==2):		
			h=h+1
	if(h>19):
		h=19
		
	for i in reversed(range(0,len(term_matrix))):
		if(h-i<0):
			return [None,-1]
		for j in range(0, len(term_matrix[0])):
			if(w+j>9):
				return [None,0]
			if(board[h-i][w+j]==1):
				if(term_matrix[i][j]==1):
					return [None,0]
			else:
				if(term_matrix[i][j]==1):
					board[h-i][w+j]=1
	return [board,1]


def semi_gradian_decent(board,board2):
	global lines_cleared
	old_params = get_parameters(board)
	new_params = get_parameters(board2)
	rem = removed_lines(board2)
	lines_cleared+=rem
	one_step_reward=reward(old_params,new_params,rem)
	#if (new_params[2]>19):
	#	new_params=[0,0,0,0,0,0,0,0]
	for i in range(0, len(weights)):
		if(weights[i]>= 0):
			sign = 1
		else:
			sign = -1
		weights[i] = weights[i] + alpha * old_params[i] * sign *(
				one_step_reward - old_params[i]*weights[i] + gamma * new_params[i]*weights[i])

	regularization_term = abs(sum(weights))


	if(regularization_term != 0):
		for i in range(0, len(weights)):
			weights[i] = 100 * weights[i] / regularization_term
			weights[i] = math.floor(1e4 * weights[i]) / 1e4  # Rounds the weights


def playgame():
    ram = recvall(conn);
    if(ram[:4]==b'kraj'):
        return True
    else:
        dataList=ram.decode("ascii").split("|")
        try:
            board = get_board(dataList)
            tetris_piece_id = dataList[-3]
            tetris_piece_id2= dataList[-2]
            #print_board(board)
            #print(tetris_piece_id)
            tetris_piece=get_piece(tetris_piece_id)
            tetris_piece2=get_piece(tetris_piece_id2)
            #print(tetris_piece_id,tetris_piece_id2)
            #tetris_piece="L"
            #print(tetris_piece)
            if(not deep):
                next_board,move = find_best_move(board,tetris_piece)
            else:
                next_board,move = find_best_move_deep(board,tetris_piece,tetris_piece2)			
            #print(move)
            #print_board(next_board)

            send_move(move,tetris_piece)
            semi_gradian_decent(board,next_board)
            #print(weights)
            return False
        except ValueError:
            print("greska")
            return True

def playgame_after_training():
    ram = recvall(conn);
    if(ram[:4]==b'kraj'):
        return True
    else:
        dataList=ram.decode("ascii").split("|")
        try:
            board = get_board(dataList)
            tetris_piece_id = dataList[-3]
            tetris_piece_id2= dataList[-2]
            tetris_piece=get_piece(tetris_piece_id)
            tetris_piece2=get_piece(tetris_piece_id2)			
            if(not deep):
                next_board,move = find_best_move(board,tetris_piece)
            else:
                next_board,move = find_best_move_deep(board,tetris_piece,tetris_piece2)
            global lines_cleared
            rem = removed_lines(next_board)
            lines_cleared+=rem
            send_move(move,tetris_piece)
            return False
        except ValueError:
            print("greska")
            return True


def remove_full_lines(board):
	preskoceno=0
	new_board = [ [ 0 for i in range(21) ] for j in range(21) ]
	for i in range(0,20):
		for j in range(0,10):
			new_board[i][j]==0
			
	if(board):		
		for i in reversed(range(0,20)):
			if(tbc(board,i)==True):
				preskoceno+=1
			else:
				for j in range(0,10):
					if(board[i][j]==1):
						new_board[i+preskoceno][j]=1
	return new_board
			


def find_best_move_deep(board,tetris_piece,next_piece):
    lista_bordova=[]
    lista_evaluacija=[]
    lista_poteza = []
    for i in range(0,terminos_rotate[tetris_piece]):
        br_polozaja=terminos_move[tetris_piece][i][1]-terminos_move[tetris_piece][i][0]+1
        for j in range(0,br_polozaja):
            tmp = simulate_board(board,tetris_piece,(i,j))
            tmp = remove_full_lines(tmp)
            if(tmp is not None):    
                for i2 in range(0,terminos_rotate[next_piece]):
                    br_polozaja2=terminos_move[next_piece][i2][1]-terminos_move[next_piece][i2][0]+1
                    for j2 in range(0,br_polozaja2):
                        tmp2 = simulate_board(tmp,next_piece,(i2,j2))
                        if(tmp2 is not None):
							#print_board(tmp)
							#print(i,j)
                            eval_val = eval(tmp2)
							#print(eval_val)
                            lista_bordova.append(tmp)
                            lista_evaluacija.append(eval_val)
                            lista_poteza.append((i,j))

    if(len(lista_evaluacija)==0):
        return board,(0,0)
    max_eval = max(lista_evaluacija)
    ind=lista_evaluacija.index(max_eval)
    best_move = lista_poteza[ind]
    best_board = lista_bordova[ind]

    if random.random() < explore_change:
        rand = random.randint(0, len(lista_poteza) - 1)
        move = lista_poteza[rand]
        best_board = lista_bordova[rand]
    else:
        move = best_move
    return best_board,move


	
if __name__=="__main__":
	waitForConnection()
	if(training):
		for i in range(0,MAX_GAMES):
			br_igara+=1
			lines_cleared=0
			while(True):
				if(playgame()):
					break;
		print("Game player %d lines cleared %d" %(br_igara,lines_cleared))   
        
		
		f= open("weights.txt","a")
		f.write("[%f , %f ,%f, %f ,%f, %f, %f, %f]\n" %( weights[0] ,weights[1],weights[2], weights[3],weights[4] ,weights[5],weights[6], weights[7]))
		f.close()
	if(avg):
		lines_cleared=0
		for i in range(0,5):
			while(True):
				if(playgame_after_training()):
					break;
		print("AVG score %f" %(lines_cleared/5))   
	if(play):
		while(True):
			if(playgame_after_training()):
				break;
	
	exit(0)