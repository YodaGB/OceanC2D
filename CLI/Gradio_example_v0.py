# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 22:44:41 2023

@author: Goutam
"""

import gradio as gr
import pickle
def publish_dataset_allow(recipientAddress,fileURI,dataset_name,allowed_algo_DID):
    import sys

    from ocean_lib.web3_internal.utils import connect_to_network
    connect_to_network("polygon-test") # mumbai is "polygon-test"
    import os
    from ocean_lib.example_config import get_config_dict
    from ocean_lib.services.service import Service
    from ocean_lib.ocean.ocean import Ocean
    from ocean_lib.ocean.util import to_wei
    config = get_config_dict("polygon-test")
    ocean = Ocean(config)
    OCEAN = ocean.OCEAN_token
    from brownie.network import accounts
    accounts.clear()

    alice_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    alice = accounts.add(alice_private_key)
    assert alice.balance() > 0, "Alice needs MATIC"
    assert OCEAN.balanceOf(alice) > 0, "Alice needs OCEAN"


    from ocean_lib.structures.file_objects import UrlFile
#Need to attach a compute service for this
# Create and attach the Service

    DATA_url_file = UrlFile(fileURI)


    name = dataset_name
    (data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, DATA_url_file.url, {"from": alice}, wait_for_aqua=True)

#Need to add compute service to the dataset and allow it to be
#executed by the specified algorithm
    DATA_files = [DATA_url_file]
    DATA_ddo = ddo
    compute_values = {
                "allowRawAlgorithm": False,
                "allowNetworkAccess": True,
                "publisherTrustedAlgorithms": [],
                "publisherTrustedAlgorithmPublishers": [],
            }

    compute_service = Service(
            "2",
            "compute",
            ocean.config_dict["PROVIDER_URL"],
            datatoken.address,
            DATA_files,
            0,
            compute_values,
        )

    ddo.add_service(compute_service)

    ddo = ocean.assets.update(ddo, {"from": alice})
# NOTE :: Minting datatoken for bob's use
#   bob's address is hard coded. When making command line
# This should be passed as args. Also, multiple addresses can be issued
# data tokens.
#bob = "0xDF9bC869CC5E81887E95Fb3B83861A372408CA6F"
    datatoken.mint(recipientAddress, to_wei(1), {"from": alice})
# Allowing Algorithm


    ALGO_ddo = ocean.assets.resolve(allowed_algo_DID)
    added_service = ddo.services[1]
    added_service.add_publisher_trusted_algorithm(ALGO_ddo) 
    ddo = ocean.assets.update(ddo, {"from": alice})

    print("Just published asset:")
    print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
    print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
    print(f"  did={ddo.did}")
    return ddo.did
def monitor_csv(dataDID,job_id):
    from ocean_lib.web3_internal.utils import connect_to_network
    connect_to_network("polygon-test") # mumbai is "polygon-test"
    import os, sys
    import numpy as np
    import time
    from sklearn import linear_model

    from ocean_lib.example_config import get_config_dict
    from ocean_lib.ocean.ocean import Ocean
    from ocean_lib.services.service import Service
    from ocean_lib.ocean.util import to_wei
    config = get_config_dict("polygon-test")
    ocean = Ocean(config)
    OCEAN = ocean.OCEAN_token
    from brownie.network import accounts

    accounts.clear()

    bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
    bob = accounts.add(bob_private_key)
    assert bob.balance() > 0, "Bob needs MATIC"
    assert OCEAN.balanceOf(bob) > 0, "Bob needs OCEAN"
#dataDID = "did:op:a57345a2b06ad55f52c0640c2223d0a88b4fd7c10c10923d3865038e08ad58e1"
    DATA_ddo = ocean.assets.resolve(dataDID)
#ALGO_ddo = ocean.assets.resolve(algoDID)
#job_id = '57cac7f1430447f993f4c20a6df0befc'
    compute_service = DATA_ddo.services[1]


    from decimal import Decimal
    succeeded = False
    

    for _ in range(0, 200000):
        status = ocean.compute.status(DATA_ddo, compute_service, job_id, bob)
    #print("Status of Job ",status)
        if status.get("dateFinished") and Decimal(status["dateFinished"]) > 0:
        #print("Job Finished")
            succeeded = True
            break
        time.sleep(5)
    result =ocean.compute.result(DATA_ddo, compute_service, job_id,1,bob)

    output = ocean.compute.compute_job_result_logs(
    DATA_ddo, compute_service, job_id, bob
)[0]
    return  output
def execute_compute(dataDID,algoDID):
    from ocean_lib.web3_internal.utils import connect_to_network
    connect_to_network("polygon-test") # mumbai is "polygon-test"
    import os
    from ocean_lib.example_config import get_config_dict
    from ocean_lib.ocean.ocean import Ocean
    from ocean_lib.services.service import Service
    from ocean_lib.ocean.util import to_wei
    config = get_config_dict("polygon-test")
    ocean = Ocean(config)
    OCEAN = ocean.OCEAN_token
    from brownie.network import accounts

    accounts.clear()

    bob_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY2')
    bob = accounts.add(bob_private_key)
    assert bob.balance() > 0, "Bob needs MATIC"
    assert OCEAN.balanceOf(bob) > 0, "Bob needs OCEAN"
# Note below the did is the one received as output of 
# publisg data set
# Operate on updated and indexed assets
    DATA_ddo = ocean.assets.resolve(dataDID)
    ALGO_ddo = ocean.assets.resolve(algoDID)

    compute_service = DATA_ddo.services[1]
    algo_service = ALGO_ddo.services[0]
    free_c2d_env = ocean.compute.get_free_c2d_environment(compute_service.service_endpoint)
    
    from datetime import datetime, timedelta
    from ocean_lib.models.compute_input import ComputeInput

    DATA_compute_input = ComputeInput(DATA_ddo, compute_service)
    ALGO_compute_input = ComputeInput(ALGO_ddo, algo_service)

# Pay for dataset and algo for 1 day
    datasets, algorithm = ocean.assets.pay_for_compute_service(
    datasets=[DATA_compute_input],
    algorithm_data=ALGO_compute_input,
    consume_market_order_fee_address=bob.address,
    tx_dict={"from": bob},
    compute_environment=free_c2d_env["id"],
    valid_until=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
    consumer_address=free_c2d_env["consumerAddress"],
)
    assert datasets, "pay for dataset unsuccessful"
    assert algorithm, "pay for algorithm unsuccessful"

# Start compute job
    job_id = ocean.compute.start(
    consumer_wallet=bob,
    dataset=datasets[0],
    compute_environment=free_c2d_env["id"],
    algorithm=algorithm,
)
    print(f"Started compute job with id: {job_id}")
    return job_id
def create_result(dataDID,job_id):

    print("Monitoring Starts..")
    import time

    timestr = time.strftime("%Y%m%d-%H%M%S")

    output = monitor_csv(dataDID,job_id)

    print("Monitoring Complete.")
#print("result:: ",result)

    print("output Type",type(output))
    output_data = str(output,'UTF-8')
    return output_data

    
#publish_dataset_allow(recipient address(hardcoded),fileURI(Gradio Input),dataset_name,allowed_algo_DID (hardcoded)
def csv_stats(URI):
    algo_did = "did:op:b13a565b66d05821478d4012ca40f0151c2de71b160a3a55dbcad649a7408214"
    did= publish_dataset_allow("0x427101Aee61E77dc22386f0ae944d687FE062b60",URI,"Weather",algo_did)
    jobid = execute_compute(did,algo_did)
    result =create_result(did,jobid)
    return result

def check_LR_Result(area):
    pkl_file = "/home/ubuntu/LR_Dump1.pkl"
    with open(pkl_file , 'rb') as f:
        lr = pickle.load(f)
        return lr.predict([[area]])

    


title = "Zero2AI Auto Execute"
description = "Auto Execution of Algorithms using your own data"
article="Linear regression - Please input an area of house to predict it.s price.Please pass an URL ofor base statistics on your dataset."



#gpt2 = gr.Interface.load("huggingface/gpt2-large")
#gptj6B = gr.Interface.load("huggingface/EleutherAI/gpt-j-6B")

def fn(model_choice, input):
  if model_choice=="Linear Regression":
    return check_LR_Result(float(input))
  elif model_choice=="CSV Stats":
    return csv_stats(input)

demo = gr.Interface(fn, [gr.inputs.Dropdown(["Linear Regression", "CSV Stats"]), "text"], "text", title=title, description=description, article=article).queue()
demo.launch(share=True)