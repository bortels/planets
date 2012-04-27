#!/usr/local/bin/lua
io.stdout:write("Content-Type: text/plain\r\n\r\n")
io.stdout:write("Hello, world! (Lua)\r\n")
for k, v in pairs(arg) do
        io.stdout:write(tostring(k), ": ", tostring(v), "\r\n")
end
io.stdout:write("PATH=" .. os.getenv("PATH") .. "\r\n")
vars = { 'SERVER_SOFTWARE', 'SERVER_NAME', 'GATEWAY_INTERFACE',
        'SERVER_PROTOCOL', 'SERVER_PORT', 'REQUEST_METHOD',
        'PATH_INFO', 'PATH_TRANSLATED', 'SCRIPT_NAME',
        'QUERY_STRING', 'REMOTE_HOST', 'REMOTE_ADDR',
        'AUTH_TYPE', 'REMOTE_USER', 'REMOTE_IDENT',
        'CONTENT_TYPE', 'CONTENT_LENGTH', 'HTTP_USER_AGENT',
}
for _, e in ipairs(vars) do
        v = os.getenv(e) or ''
        io.stdout:write(e .. "=" .. v .. "\r\n")
end
