from myhtml import *
import sys
import os
import shutil

indent = " "*4
page = Page(sys.argv[1])
page.scanPage()
#out=sys.stdout
#page.dump(out)
pageContainer = page.pageContainer
if len(pageContainer.subElemList) > 1:
    print "more than 1 top container exists"
    sys.exit()
xmlContainer = pageContainer.subElemList[0]
if xmlContainer.name != "xml":
    print "Top container is not xml!"
    sys.exit()

ctype="uint8_fff"
rpctype="Integer"
length="1"

def getTypeAndLength(paramType):
    global ctype
    global rpctype,length
    ctype = paramType+"_t"
    rpcType = "Integer"
    if paramType == "uint8":
        length = "1"
    elif paramType == "int8":
        length = "1"
    elif paramType == "uint16":
        length = "2"
    elif paramType == "int16":
        length = "2"
    elif paramType == "uint32":
        length = "4"
    elif paramType == "int32":
        length = "4"
    elif paramType == "uint64":
        length = "8"
    elif paramType == "int64":
        length = "8"
    elif paramType == "buf":
        ctype = "uint8_t *"
        rpctype = "Buffer"
    

def codeGenPrimitivePart1(intf, out):
    out.write(intf.attrs["returntype"] + " " + intf.attrs["name"] + "(\n")
    for i in range(len(intf.subElemList)):
        param = intf.subElemList[i]
        if param.name != "param":
            continue
        getTypeAndLength(param.attrs["type"])
        out.write(indent + ctype + " ")
        if param.attrs.has_key("out") and param.attrs["out"] == "1":
            out.write("*")
        out.write(param.attrs["name"])
        if i<len(intf.subElemList)-1:
            out.write(",\n")
        else:
            out.write(") {\n")

def codeGenPrimitivePart2(intf, out):
    if intf.attrs["returntype"] == "int":
        out.write(indent + "return 0;\n")
    out.write("}\n\n")

def codeGenRpcClient(intf):
    dirname = "rpc_gen_" + intf.attrs["client"] 
    filename = dirname + "/" + "rpc_gen_client.c"
    out = open(filename, "w+")

    out.write("//client\n");
    codeGenPrimitivePart1(intf, out)
    out.write("\n")

    out.write(indent + "Rpc_Context_t *ctx = rpc_ctx_alloc(Rpc_Ctx_Scale_Normal);\n")
    out.write(indent + "Rpc_Message_t *req = ctx->rpcMsgReq;\n")
    out.write(indent + "Rpc_Message_t *resp = ctx->rpcMsgResp;\n")
    out.write("\n")

    out.write(indent + "//Encode request message\n");
    for param in intf.subElemList:
        getTypeAndLength(param.attrs["type"])
        if not param.attrs.has_key("out") or param.attrs["out"] != "1":
            out.write(indent + "rpc_encode(req, ")
            out.write("Rpc_Encoding_Type_" + rpctype + ", ")
            out.write(length + ", ")
            out.write("&" + param.attrs["name"] + ");\n")
    out.write("\n")

    out.write(indent + "//Send request\n")
    out.write(indent + "rpc_ctx_req(ctx);\n")
    out.write("\n")

    out.write(indent + "//Wait response\n")
    out.write(indent + "rpc_ctx_wait_resp(ctx);\n")
    out.write("\n")

    out.write(indent + "//Decode response message\n")
    for param in intf.subElemList:
        if param.name == "param" and param.attrs.has_key("out") and param.attrs["out"]=="1":
            out.write(indent + "rpc_decode(resp, &" + param.attrs["name"] + ");\n")
    out.write("\n")
    codeGenPrimitivePart2(intf, out)
    out.close()

def codeGenRpcServerAgent(intf):
    dirname = "rpc_gen_" + intf.attrs["server"] 
    filename = dirname + "/" + "rpc_gen_server_agent.c"
    out = open(filename, "w+")

    out.write("//server agent\n");
    out.write("Rpc_ReturnType " + intf.attrs["name"] + "_RpcServerAgent(\n")
    out.write(indent + "Rpc_Context_t *ctx) {\n")
    out.write("\n")

    out.write(indent + "Rpc_Message_t *req = ctx->rpcMsgReq;\n")
    out.write(indent + "Rpc_Message_t *resp = ctx->rpcMsgResp;\n")
    out.write("\n")

    out.write(indent + "//Decode request message\n")
    for param in intf.subElemList:
        getTypeAndLength(param.attrs["type"])
        out.write(indent + ctype + " " + \
            param.attrs["name"] + ";\n")
        if not param.attrs.has_key("out") or param.attrs["out"] != "1":
            out.write(indent + "rpc_decode(req, &" + param.attrs["name"] + ");\n")
        out.write("\n")

    out.write(indent + "//Call server primitive function\n");
    out.write(indent + intf.attrs["name"] + "(\n")
    for i in range(len(intf.subElemList)):
        param = intf.subElemList[i]
        out.write(indent*2)
        if param.attrs.has_key("out") and param.attrs["out"] == "1":
            out.write("&")
        out.write(param.attrs["name"])
        if i<len(intf.subElemList)-1:
            out.write(",\n")
        else:
            out.write(");\n")
    out.write("\n")

    out.write(indent + "//Encode result to response message\n")
    for param in intf.subElemList:
        if param.name == "param" and param.attrs.has_key("out") and param.attrs["out"]=="1":
            getTypeAndLength(param.attrs["type"])
            out.write(indent + "rpc_encode(resp, ")
            out.write("Rpc_Encoding_Type_" + rpctype + ", ")
            out.write(length + ", ")
            out.write("&" + param.attrs["name"] + ");\n")
    out.write("\n")

    out.write("}\n")

    out.write("\n")
    out.close()

def codeGenRpcServerPrimitive(intf):
    dirname = "rpc_gen_" + intf.attrs["server"] 
    filename = dirname + "/" + "rpc_gen_server_primitive.c"
    out = open(filename, "w+")

    out.write("//server primitive\n");
    codeGenPrimitivePart1(intf, out)
    codeGenPrimitivePart2(intf, out)

    out.close()

def codeGenRpcInterface():
    for intf in xmlContainer.subElemList:
        if intf.name != "interface":
            continue

        codeGenRpcClient(intf)
        codeGenRpcServerAgent(intf)
        codeGenRpcServerPrimitive(intf)
        #break

def codeGenRpcCommon():
    dirname = "rpc_gen_" + "common"
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.mkdir(dirname)
    filename = dirname + "/" + "rpc_gen_common_cfg.c"
    out = open(filename, "w")

    out.write("#include \"rpc_cfg.h\"\n")
    out.write("\n")

    out.write("Rpc_Cfg_Node_t rpc_cfg_nodes[] = {\n")

    isNotFirst = False
    for node in xmlContainer.subElemList:
        if node.name != "node":
            continue
        if isNotFirst:
            out.write(",\n")
        dirname = "rpc_gen_" + node.attrs["name"]
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)
        out.write(indent + "{\n")
        out.write(indent*2 + ".type = " + node.attrs["type"] + ",\n")
        out.write(indent*2 + ".id = " + node.attrs["id"] + ",\n")
        out.write(indent*2 + ".name = \"" + node.attrs["name"] + "\",\n")
        if node.attrs["type"] == "socket":
            for s in node.subElemList:
                if s.name != "socket":
                    continue
                out.write(indent*2 + ".socket = {\n")
                out.write(indent*3 + ".addr = \"" + s.attrs["addr"] + "\",\n")
                out.write(indent*3 + ".port = " + s.attrs["port"] + "\n")
                out.write(indent*2 + "}")
        
        out.write("\n")
        out.write(indent + "}")
        isNotFirst = True

    out.write("\n")
    out.write("};\n")
    out.close()
    
codeGenRpcCommon()
codeGenRpcInterface()
