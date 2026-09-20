#!/usr/bin/env python3
"""Validate the selected bank model with its independent decoder."""
import argparse
import json
from pathlib import Path
from bank_routing import model

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("file",type=Path)
    args=parser.parse_args()
    try:
        data=json.loads(args.manifest.read_text(encoding="utf-8"))
        print(json.dumps(model(data).validate(data,args.file.read_bytes()),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,str(exc)+"\n")

if __name__=="__main__":
    main()
