import base64
from nacl.public import PrivateKey
import os
import stat
import sys


def gen_private_key(Filepath: str):
    """Generate a random secret key (as base64 encoded string)"""
    # should be sufficiently random as it implements entropy-driven
    # random sources available on the host (e.g. /dev/random)
    RandBytes = os.getrandom(32)

    StrKey = base64.b64encode(RandBytes)

    PrivateKeyPath = f"{Filepath}.key"
    with open(PrivateKeyPath, "wb") as File:
        File.write(StrKey)

    print(f"Generated: {PrivateKeyPath}")
    os.chmod(PrivateKeyPath, stat.S_IRUSR | stat.S_IWUSR)


def gen_public_key(GivenPath: str):
    """Generate a public key given a private key"""
    Filepath = GivenPath + ".key"

    if os.path.exists(Filepath) and os.path.isfile(Filepath):
        Filename = os.path.basename(Filepath)
        Filenameext = os.path.splitext(Filename)

        if str.lower(Filenameext[1]) != ".key":
            print(f"{Filepath} is not a secret .KEY file!")
            exit(1)

        # base64 encoded private key
        StrSecret: str
        with open(Filepath, "r") as File:
            StrSecret = File.readline()

        # generate private-public keypair
        SecretBytes = base64.b64decode(StrSecret)
        SecretKey = PrivateKey(SecretBytes)
        PublicKey = SecretKey.public_key._public_key

        # base64 encoded public key
        StrPublic = base64.b64encode(PublicKey).decode("utf-8")

        Filedir = os.path.dirname(os.path.abspath(Filepath))

        PubkeyFilepath = f"{Filedir}/{Filenameext[0]}.pub"
        with open(PubkeyFilepath, "w") as File:
            File.write(StrPublic)

        print(f"Generated: {PubkeyFilepath}")
        os.chmod(PubkeyFilepath, stat.S_IRUSR | stat.S_IWUSR)

    else:
        print(f"File not found: {Filepath}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: gen_key [private|public|pair] <KEYFILE>\n")
        print("\t[private|public|pair]:")
        print("\t\t - Select the type of key to generate")
        print("\t\t - 'public' needs an existing private keyfile!\n")
        print("\t\t - 'pair' automatically generates both files\n")
        print("\tKEYFILE:")
        print("\t\t- name of the keyfile to generate (e.g. keys/mysecretkey)")
        exit(0)

    GenType = sys.argv[1]

    if GenType.lower() == "private":
        gen_private_key(sys.argv[2])

    elif GenType.lower() == "public":
        gen_public_key(sys.argv[2])

    elif GenType.lower() == "pair":
        gen_private_key(sys.argv[2])
        gen_public_key(sys.argv[2])

    else: 
        print(f"Wrong key type: {GenType}")