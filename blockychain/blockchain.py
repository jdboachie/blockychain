import hashlib
import json
import requests
from time import time
from uuid import uuid4
from typing import Optional
from textwrap import dedent
from urllib.parse import urlparse


class Blockchain(object):
    def __init__(self):
        self.chain: list = []
        self.nodes: set = set()
        self.current_transactions: list = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self,
                  proof: int,
                  previous_hash: Optional[str]) -> dict:
        """Create a new Block in the Blockchain

        Args:
            proof (int): the proof given by the proof of work algorithm
            previous_hash (Optional[str]): hash of previous Block

        Returns:
            dict: new Block
        """

        block = {
            'index': uuid4(),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self,
                        sender: str,
                        recipient: str,
                        amount: int) -> int:
        """Creates a new transaction to go into the next mined Block

        Args:
            sender (str): address of the sender
            recipient (str): address of the recipient
            amount (int): amount

        Returns:
            int: the index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof: int) -> int:
        """Simple PoW Algorithms:
        - Find a number p' such that hash(pp') contains 4 leading zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof

        Args:
            last_proof (int): previous proof

        Returns:
            int: proof
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def hash(block: dict) -> str:
        """Creates a SHA-256 hash of a Block

        Args:
            block (dict): Block

        Returns:
            str: hash
        """

        # We must make sure the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        print(hash)
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """Validates the Proof: does the hash(last_proof, proof) contain 4 leading zeroes?

        Args:
            last_proof (int): Previous proof
            proof (int): Current proof

        Returns:
            bool: True if correct, False is not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def valid_chain(self, chain: list) -> bool:
        """Determine if a given blockchain is valid

        Args:
            chain (list): A blockchain

        Returns:
            bool: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """This is my Consensus Algorithm, it resolves conflicts by
        replacing the chain with the longest one in the network.

        Returns:
            bool: True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in the network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @property
    def last_block(self) -> dict:
        """Returns the last Block in the Blockchain

        Returns:
            dict: Block
        """
        self.chain[-1]

    def register_node(self, address: str) -> None:
        """Adds a new node to the list of nodes

        Args:
            address (str): Address of node. Eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
