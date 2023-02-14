                if int(accuracy)>=65: 
                    serverMessage = 'Validated!Accuracy = '+accuracy+ '%'
                    checked.append(Client_Num)
                else:
                    serverMessage = 'Fail!Accuracy = '+accuracy+ '%'
                    
                    
                    
                if len(done) == 2:
                    # [ Only one client passes the validation]
                    if len(checked)==1: 
                        IPFS=[]
                        path = 'hash.txt'
                        with open(path) as f:
                            IPFS = f.readlines()

                        if checked[0]=="8081":
                            LM_IPFS = IPFS[0].replace("\n", "")
                        else :
                            LM_IPFS = IPFS[1].replace("\n", "")
                        print(LM_IPFS)
                        serverMessage = 'Next Global Model hash:'+ LM_IPFS

                    # [ Nobody passes the validation ]
                    elif len(checked)==0:
                        path = '/workspaces/Blockchain-based-Federated-Learning/BCFL/latest_GMhash.txt'
                        if not path in os.listdir('/workspaces/Blockchain-based-Federated-Learning/BCFL'):
                            IPFS=[]
                            with open('/workspaces/Blockchain-based-Federated-Learning/BCFL/hash.txt','r') as f:
                                IPFS = f.readlines()
                            f = open(path,"w")
                            LM_IPFS = IPFS[0].replace("\n", "")
                            f.write(LM_IPFS)
                        else:
                            f = open(path, 'r')
                            LM_IPFS = f.read()
                            f.close()
                        serverMessage = 'Next Global Model hash:'+ LM_IPFS
                    
                    # [ >1 clients pass the validation, need to aggregate global model weight]
                    else:
                        print("Aggregating...")
                        LM_IPFS = aggregated(checked)
                        serverMessage = 'Next Global Model hash:'+ LM_IPFS