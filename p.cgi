#!/usr/bin/env lua

local redis = require 'redis'
local client = redis.connect('127.0.0.1', 6379)
local now = os.time()
auth=false

print "Content-type: text/plain\n"

function round(num, idp)
  local mult = 10^(idp or 0)
  return math.floor(num * mult + 0.5) / mult
end

function dumptable(t)
   local out = ''
   local k,v
   for k,v in pairs(t) do
      out = out .. k .. ' ' .. v .. "\n"
   end
   return out
end

function urldecode(s)
  return (string.gsub(string.gsub(s, '+', " "),
     "%%(%x%x)",
     function (str)
        return string.char (tonumber (str, 16))
     end))
end -- function urldecode

function requireauth()
   if (auth == false) then
      print("ERROR Session expired or login failed")
      print(debuginfo)
      do return end
   end
end

function printhash(key)
   local h = client:hgetall(key)
   io.write(dumptable(h))
end

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
io.stderr:write(dumptable(post))
sid = post.sid or "BOGUS"
user = "---"
skey = "session-" .. sid 
ttl = client:ttl(skey)
auth = ttl > 0
if (auth) then -- refresh the session
   client:expire("session-" .. sid, 15*60)
   user = client:hget(skey, "user")
   ip = client:hget(skey, "ip")
end

if (post.cmd == nil) then
   print "ERROR cmd is a required parameter"
   do return end
end

if (post.cmd == "login") then
   user = post.user or ''
   pass = post.pass or ''
   p = client:hget("player-" .. user, "pass")
   if (p == pass) then
      math.randomseed( os.time() ) -- TODO consider lrandom and a way better seed.
      s = math.random(99999999999999) .. math.random(99999999999999) .. math.random(99999999999999) -- crude, but effective
      skey = "session-" .. s
      client:hmset(skey, "user", user, "ip", os.getenv ("REMOTE_ADDR"))
      client:expire(skey, 15*60)
      io.write(s)
      do return end
   else
      print "ERROR Bad Login"
      do return end
   end
end

if (post.cmd == "gameinfo") then
   requireauth()
   if (post.game) then
      if (client:exists(post.game .. "-info")) then
         printhash(post.game .. "-info")
         printhash(post.game .. "-players")
--         local obs = client:smembers(post.game .. '-objects')
--         io.write("visible " .. table.concat(obs, ' '))
         do return end
      else
         print("ERROR game " .. post.game .. " does not exist")
         do return end
      end
   else
      print("ERROR game is a required parameter")
      do return end
   end
end

if (post.cmd == "visible") then
   requireauth()
   if (post.game) then
      local obs = client:smembers(post.game .. '-objects')
      for _,v in pairs(obs) do
         local o = client:hgetall(post.game .. '-' .. v)
         io.write(v .. ' ' .. o.player .. ' ' .. o.x .. ' ' ..  o.y .. ' ' .. o.type .. ' ' .. o.name .. "\n")
      end
      do return end
   else
      print("ERROR game is a required parameter")
      do return end
   end
end

if (post.cmd == "join") then
   requireauth()
   if (post.game) then
      if (client:exists(post.game .. "-info")) then
         --# $r.sadd "#{game}-players", user  # TODO this needs to be added to the hash
      end
   end
   printhash(post.game .. "-players")
end

if (post.cmd == "msg") then
   requireauth()
   if (post.to) then
      if (post.body) then
          -- TODO figure out how we store these elegantly
      else
         print("ERROR 'body' is a required parameter") 
      end
   else
      print("ERROR 'to' is a required parameter")
      do return end
   end
end

if (post.cmd == "info") then
   requireauth()
   if (post.object == nil) then
      print("ERROR 'object' is a required parameter")
      do return end
   end
   if (post.game == nil) then
      print("ERROR 'game' is a required parameter")
      do return end
   end
   printhash(post.game .. '-' .. post.object)
   do return end
end


if (post.cmd == "rename") then
   requireauth()
   if (post.name == nil) then
      print("ERROR 'name' is a required parameter")
      do return end
   end
   if (post.object == nil) then
      print("ERROR 'object' is a required parameter")
      do return end
   end
   if (post.game == nil) then
      print("ERROR 'game' is a required parameter")
      do return end
   end
   -- confirm this player owns the object to be renamed
   local info = client:hgetall(post.game .. '-' .. post.object)
   local player = info.player 
   local gameinfo = client:hgetall(post.game .. '-players')
   if (post.user == gameinfo.player) then
      client.hset(post.game .. '-' .. post.object, 'name', post.name)
      printhash(post.game .. '-' .. post.object)
      do return end
   else
      print("ERROR you don't seem to own that object")
      do return end
   end
end

if (post.cmd == "waypoint") then
   requireauth()
   if (post.x == nil) then
      print("ERROR 'x' is a required parameter")
      do return end
   end
   if (post.y == nil) then
      print("ERROR 'x' is a required parameter")
      do return end
   end
   if (post.object == nil) then
      print("ERROR 'object' is a required parameter")
      do return end
   end
   if (post.game == nil) then
      print("ERROR 'game' is a required parameter")
      do return end
   end
   -- confirm this player owns the object to be renamed
   local info = client:hgetall(post.game .. '-' .. post.object)
   local player = info.player
   local gameinfo = client:hgetall(post.game .. '-players')
   if (post.user == gameinfo.player) then
      client.hset(post.game .. '-' .. post.object, 'wpx', post.x)
      client.hset(post.game .. '-' .. post.object, 'wpy', post.y)
      printhash(post.game .. '-' .. post.object)
      do return end
   else
      print("ERROR you don't seem to own that object")
      do return end
   end
end

if (post.cmd == "debug") then
   print(dumptable(post))
   do return end
end

print("ERROR: unrecognized command " .. post.cmd)
do return end


--[[ Old code here for reference

function loadgame(g)
   info = client:hgetall(g .. "-info")
   if (now - info['rollover'] > 0) then
      rungame(g)
   else
      print('game ' .. g .. ' runs in ' .. info.rollover - now .. ' seconds')
   end 
end

function doplanet(p)
   -- population growth
   local pop = p.pop or 0
   pop = round(pop * 1.01)
   p.pop = pop
   -- manufacturing
end

function doship(s)
   -- base visibility
   vis = 1
   if (s.basevis) then vis = s.basevis end
   -- movement
   local speed = tonumber(s.speed)
   if (speed > 0) then
      local x1 = s.x
      local y1 = s.y
      local x2 = s.wpx
      local y2 = s.wpy
      local speed = s.speed
      -- math is fun
      local dist2 = (y2 -y1) ^ 2 + (x2 - x1) ^ 2
      if (dist2 < 0.1) then vis = vis / 2 end -- not moving is stealthy
      if (speed ^ 2 > dist2) then 
         s.x = s.wpx
         s.y = s.wpy
         print('ship ' .. s.name .. ' has arrived at the waypoint')
      else
         local angle = math.atan2(y2 - y1, x2 - x1)
         local dx = math.cos(angle) * speed
         local dy = math.sin(angle) * speed
         s.x = round(s.x + dx)
         s.y = round(s.y + dy)
         print('ship ' .. s.name .. ' moved from (' .. x1 .. ',' .. y1 .. ') to (' .. s.x .. ',' .. s.y .. ')')
      end
   else
      vis = vis / 2 -- not moving is stealthy
   end -- if (s.speed > 0)
   s.vis = vis
end

function rungame(g)
   print("running game " .. g .. " '" .. info['name'] .. "'")
   obs = client:smembers(g .. "-objects")
   things = {}
   -- load all the things!
   for _, v in pairs(obs) do
      things[v] = client:hgetall(g .. '-' .. v)
   end
   -- do all the things!
   for _, v in pairs(obs) do
      if (things[v]['type'] == 'planet') then doplanet(things[v]) end
      if (things[v]['type'] == 'ship')   then doship(things[v])   end
   end
   -- save all the things!
   for _, v in pairs(obs) do
      client:hmset(g .. '-' .. v, things[v])
   end
   -- TODO cull any dead objects (has "dead" property)
   -- TODO update game info (new rollover)
   client:hset(g .. "-info", "rollover", info.rollover + info.turnlen)  
   -- client:hset(g .. "-info", "rollover", now + info.turnlen)
end

-- dump client info
function dumpinfo()
   for k,v in pairs(client:info()) do
      print(k)
      for i,j in pairs(v) do
         print('    ' .. i .. ' => ' .. tostring(j))
      end
   end
end

-- main
games = client:smembers("games")
for _,v in ipairs(games) do
   loadgame(v)
end

====================web============================


 ]]-- 
