#!/usr/bin/env lua

local redis = require 'redis'
local client = redis.connect('127.0.0.1', 6379)
local now = os.time()

print "Content-type: text/plain\n\n"

function round(num, idp)
  local mult = 10^(idp or 0)
  return math.floor(num * mult + 0.5) / mult
end

function dumptable(t)
   local k,v
   for k,v in pairs(t) do
      print(k .. ' => ' .. v)
   end
end

function urldecode(s)
  return (string.gsub(string.gsub(s, '+', " "),
     "%%(%x%x)",
     function (str)
        return string.char (tonumber (str, 16))
     end))
end -- function urldecode

-- parse POSTed data, if any
local post = {}
local post_length = tonumber (os.getenv ("CONTENT_LENGTH")) or 0
if os.getenv ("REQUEST_METHOD") == "POST" and post_length > 0 then
   local body = io.read(post_length)
   local token, k, v
   for token in string.gmatch(body, "[^&]+") do
      for k, v in string.gmatch(token, "(.-)=(.+)") do
         post[urldecode(k)] = urldecode(v)
      end
   end
else
   print("ERROR No posted data")
   do return end
end -- if post

-- On with the show!
dumptable(post)

--[[ Old code here for reference

else
  sampleform = [===[
  <form action="/p/" method="post">
  LOGIN:
  cmd: <input type="text" name="cmd" value="login"/><br />
  user: <input type="text" name="user" /><br />
  pass: <input type="text" name="pass" /><br />
  <input type="submit" value="Submit" />
  </form>
  <hr>
  <form action="/p/" method="post">
  GAMEINFO:
  cmd: <input type="text" name="cmd" value="gameinfo"/><br />
  sid: <input type="text" name="sid" /><br />
  game: <input type="text" name="game" /><br />
  <input type="submit" value="Submit" />
  </form>
  <hr>
  <form action="/p" method="post">
  cmd: <input type="text" name="cmd"/><br />
  sid: <input type="text" name="sid" /><br />
  a1: <input type="text" name="a1" /><br />
  a2: <input type="text" name="a2" /><br />
  a3: <input type="text" name="a3" /><br />
  a4: <input type="text" name="a4" /><br />
  a5: <input type="text" name="a5" /><br />
  a6: <input type="text" name="a6" /><br />
  a7: <input type="text" name="a7" /><br />
  a8: <input type="text" name="a8" /><br />
  a9: <input type="text" name="a9" /><br />
  <input type="submit" value="Submit" />
  </form> ]===]
  print("Content-type: text/html\n\n" .. sampleform)
end

post '/p/' do
  content_type "text/plain"

  # Session management
  sid = params[:sid] || 'BOGUS'
  $user = "---"
  skey = "session-" + sid
  ttl = $r.ttl skey
  $auth = ttl > 0
  if ($auth) then # refresh the session
     $r.expire "session-" + sid, 15*60
     $user = $r.hget skey, "user"
     ip = $r.hget skey, "ip"
     #puts "user " + $user + " just came back " + ip + " vs " + request.ip
  end
  # puts skey + " ttl is " + ttl.to_s + " and auth is " + $auth.to_s

  case params[:cmd]

  when "login"
     user = params[:user] || ''
     pass = params[:pass] || '' # TODO we should save a hash, not the pass
     p = $r.hget "player-#{user}", "pass"
     # puts "pass for #{user} in database is #{p} compared with #{pass}"
     if (p == pass) then
        s = rand(36**16).to_s(36)
        skey = "session-" + s
        $r.hmset skey, "user", user, "ip", request.ip
        $r.expire skey, 15*60
        $user=user
        plog("login ok")
        halt s
     else
        plog("login fail, bad user or pass")
        halt "ERROR Bad Login"
     end

  when "gameinfo"
     requireauth()
     game = params[:game]
     if (game) then
        if ($r.exists "#{game}-info") then
           # members = $r.hgetall "#{game}-players"
           plog("gameinfo #{game}")
           halt gethash("#{game}-info") + gethash("#{game}-players")
        else
           halt "ERROR game #{game} does not exist"
        end
     else
        halt "ERROR game is a required parameter"
     end

  when "join" # join a game, "0" is random
     requireauth()
     game = params[:game]
     if (game) then
        if ($r.exists "#{game}-info") then
           plog("#{user} joined game #{game}")
           # $r.sadd "#{game}-players", user  # TODO this needs to be added to the hash
        end
     end
     halt gethash("#{game}-players")

  when "msg" # game, to, message
     requireauth()
     halt "TODO"

  when "build" # game, who, what, how many
     halt "TODO"

  else
     plog("unrecognized command " + param[:cmd])
     halt "ERROR bad cmd" 
  end
  #out = ''
  #params.keys.each do |p|
  #   out << p + ' ' + params[p] + "\n"
  #end
  "ERROR You shouldn't get here - Tell Tom he forgot a 'halt' statement"
  #return info + "objects " + objects + "\n" + "time " + Time.now.to_i.to_s + "\n"
  # @foos = redis.lrange("foos", 0, -1) # Array
  # @foos.inspect
end

get '/p/info/:game/:object' do |game, object|
  content_type "text/plain"
  gethash("#{game}-#{object}")
end

get '/p/join/:game' do |game|
   "TBI"
end

get '/p/login/:user' do |user|
end

get '/p/name/:game/:object/:name' do |game, object, name| # Maybe this should be an order...
    obj = "#{game}-#{object}"
    $r.hset obj, "name", name
end

get '/p/order/:game/:order' do |game, order|
   id = r.hincrby "#{game}-info", "nextid", 1
   r.hmset "#{game}-#{id}", "do", order, "type", "order", "player", 0
   id
end

def requireauth
   if (! $auth) then
      halt "ERROR Session expired or login failed"
   end
end

def gethash(key)
   h = $r.hgetall(key)
   output = ''
   h.keys.each do |k|
     output << k + ' ' + h[k] + "\n"
  end
  return output 
end

def plog(t)
   puts Time.now.to_i.to_s + ' ' + request.ip + ' ' + $user + ' ' + t 
end
 ]]-- 
