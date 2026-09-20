#!/usr/bin/env python3
"""Build with the explicitly selected bank model; never import into DATEV."""
import argparse
import json
from pathlib import Path
from bank_routing import model

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    try:
        data=json.loads(args.manifest.read_text(encoding="utf-8"))
        payload,report=model(data).build(data)
        sidecar=args.output.with_suffix(".pruefung.json")
        if args.output.exists() or sidecar.exists():
            raise ValueError("Output already exists; choose a clearly identified replacement version.")
        with args.output.open("xb") as stream:
            stream.write(payload)
        with sidecar.open("x",encoding="utf-8") as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,str(exc)+"\n")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
