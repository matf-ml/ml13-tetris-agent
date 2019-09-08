local socket = require("socket.core")
local move = {} ;
local inp = {};

joypad.set(1, inp)
--emu.speedmode("turbo")


function connect(address, port, laddress, lport)
    local sock, err = socket.tcp()
    if not sock then return nil, err end
    if laddress then
        local res, err = sock:bind(laddress, lport, -1)
        if not res then return nil, err end
    end
    local res, err = sock:connect(address, port)
    if not res then return nil, err end
    return sock
end


 sock2, err2 = connect("127.0.0.1", 81)
 sock2:settimeout(0)
 print("Connected", sock2, err2)




function passiveUpdate()
    local message, err, part = sock2:receive("*all")
    if not message then
        message = part
    end
    if message then
		move={}
		for i in string.gmatch(message,"%S+") do
			table.insert(move,i)
		end
    end
end


function memoryRead()
   local b="";
   for i=1024,1223 do
	   local ram = memory.readbyte(i);
	   b=b..tostring(ram);
	   b=b..'|';
   end
   -- pieceID
   local ram = memory.readbyte(66);
   b=b..tostring(ram);
   b=b..'|';
   local ram = memory.readbyte(25);
   b=b..tostring(ram);
   b=b..'|';
   sock2:send(b);
   
end


function test_for_end()
	if(memory.readbyte(72) == 10) then
		return true
	end
	return false
end


function restart_game()
	if (memory.readbyte(72) > 1) then
		set_input({'start','start','start','start'},10)
		if (memory.readbyte(0) == 0) then
		set_input({'start'},10)
		end
	end
	sock2:send("kraj")
end

function frame_advance(n)
	for i=0,n do
		emu.frameadvance()
	end
end

function set_input(commands,timer)
	for i, command in ipairs(commands) do
		inp[command]=true;
		joypad.set(1, inp)
		frame_advance(timer)
		inp={}
		joypad.set(1, inp)
		emu.frameadvance()
	end
	joypad.set(1, inp)
	emu.frameadvance()
end



function main()
	memoryRead()
    while(true) do
		if(test_for_end()) then
		--	emu.speedmode("turbo")
		 	frame_advance(240)
			restart_game()	
		else
			if(memory.readbyte(68) == 7) then
		--		emu.speedmode("normal")
			end
			passiveUpdate()
			set_input(move,1)
			if(memory.readbyte(72) > 1) then
				inp={}
				joypad.set(1, inp)
				while(memory.readbyte(72) ~=1 and memory.readbyte(72) ~= 10 ) do
					emu.frameadvance()
				end
			    if(memory.readbyte(72) == 1) then
					memoryRead()
				end
			end
		end
    	emu.frameadvance()
    end
end




main()

