#!/usr/bin/env python3
"""Batch upload files to tdrive. Processes files in groups of 5 parallel uploads."""
import subprocess
import json
import sys
import os

BASE_DIR = "/workspace/mfr-cloud-finance"

# File list: (local_rel_path, dir_id, file_name)
FILES = [
    # frontend root files -> ImkYLYGamHUj
    ("frontend/index.html", "ImkYLYGamHUj", "index.html"),
    ("frontend/.gitignore", "ImkYLYGamHUj", ".gitignore"),
    ("frontend/package.json", "ImkYLYGamHUj", "package.json"),
    ("frontend/package-lock.json", "ImkYLYGamHUj", "package-lock.json"),
    ("frontend/README.md", "ImkYLYGamHUj", "README.md"),
    ("frontend/tsconfig.json", "ImkYLYGamHUj", "tsconfig.json"),
    ("frontend/tsconfig.app.json", "ImkYLYGamHUj", "tsconfig.app.json"),
    ("frontend/tsconfig.node.json", "ImkYLYGamHUj", "tsconfig.node.json"),
    ("frontend/vite.config.ts", "ImkYLYGamHUj", "vite.config.ts"),
    # frontend/.vscode -> ISWcxjgglGvT
    ("frontend/.vscode/extensions.json", "ISWcxjgglGvT", "extensions.json"),
    # frontend/public -> IShUfHlRMunS
    ("frontend/public/favicon.svg", "IShUfHlRMunS", "favicon.svg"),
    ("frontend/public/icons.svg", "IShUfHlRMunS", "icons.svg"),
    ("frontend/public/logo.png", "IShUfHlRMunS", "logo.png"),
    # frontend/src -> IqkgFxyvkoSY
    ("frontend/src/main.ts", "IqkgFxyvkoSY", "main.ts"),
    ("frontend/src/App.vue", "IqkgFxyvkoSY", "App.vue"),
    ("frontend/src/style.css", "IqkgFxyvkoSY", "style.css"),
    # frontend/src/api -> ICVsWMFEOztP
    ("frontend/src/api/dashboard.ts", "ICVsWMFEOztP", "dashboard.ts"),
    # frontend/src/assets -> IWlqKqfqHSBl
    ("frontend/src/assets/hero.png", "IWlqKqfqHSBl", "hero.png"),
    ("frontend/src/assets/vite.svg", "IWlqKqfqHSBl", "vite.svg"),
    ("frontend/src/assets/vue.svg", "IWlqKqfqHSBl", "vue.svg"),
    # frontend/src/components -> ItxrdGfeFwZf
    ("frontend/src/components/HelloWorld.vue", "ItxrdGfeFwZf", "HelloWorld.vue"),
    # frontend/src/layouts -> IXnSSfxWftRM
    ("frontend/src/layouts/MainLayout.vue", "IXnSSfxWftRM", "MainLayout.vue"),
    # frontend/src/layouts/components -> IKdyRfhdgwZF
    ("frontend/src/layouts/components/SideNav.vue", "IKdyRfhdgwZF", "SideNav.vue"),
    ("frontend/src/layouts/components/TopBar.vue", "IKdyRfhdgwZF", "TopBar.vue"),
    # frontend/src/plugins -> IPGjaQXtUhaJ
    ("frontend/src/plugins/echarts.ts", "IPGjaQXtUhaJ", "echarts.ts"),
    # frontend/src/router -> IDFImxWNPOPV
    ("frontend/src/router/index.ts", "IDFImxWNPOPV", "index.ts"),
    # frontend/src/stores -> IHDpFxNvQTvS
    ("frontend/src/stores/app.ts", "IHDpFxNvQTvS", "app.ts"),
    # frontend/src/types -> IgJYJlqHPZjo
    ("frontend/src/types/dashboard.ts", "IgJYJlqHPZjo", "dashboard.ts"),
    # frontend/src/utils -> InlScfzpbkxB
    ("frontend/src/utils/format.ts", "InlScfzpbkxB", "format.ts"),
    # frontend/src/views/dashboard -> IxVuAMbxzLaK
    ("frontend/src/views/dashboard/Dashboard.vue", "IxVuAMbxzLaK", "Dashboard.vue"),
    # frontend/src/views/dashboard/components -> IaolRALmQxrm
    ("frontend/src/views/dashboard/components/BusinessChart.vue", "IaolRALmQxrm", "BusinessChart.vue"),
    ("frontend/src/views/dashboard/components/FundOverview.vue", "IaolRALmQxrm", "FundOverview.vue"),
    ("frontend/src/views/dashboard/components/QuickActions.vue", "IaolRALmQxrm", "QuickActions.vue"),
    ("frontend/src/views/dashboard/components/TaxChart.vue", "IaolRALmQxrm", "TaxChart.vue"),
    ("frontend/src/views/dashboard/components/VoucherCard.vue", "IaolRALmQxrm", "VoucherCard.vue"),
    # frontend/src/views/general-ledger -> ImgyWdCwBPuw
    ("frontend/src/views/general-ledger/AccountSummary.vue", "ImgyWdCwBPuw", "AccountSummary.vue"),
    ("frontend/src/views/general-ledger/AuxBalanceSheet.vue", "ImgyWdCwBPuw", "AuxBalanceSheet.vue"),
    ("frontend/src/views/general-ledger/AuxDetailLedger.vue", "ImgyWdCwBPuw", "AuxDetailLedger.vue"),
    ("frontend/src/views/general-ledger/BalanceSheet.vue", "ImgyWdCwBPuw", "BalanceSheet.vue"),
    ("frontend/src/views/general-ledger/ChronologicalLedger.vue", "ImgyWdCwBPuw", "ChronologicalLedger.vue"),
    ("frontend/src/views/general-ledger/ColumnarLedger.vue", "ImgyWdCwBPuw", "ColumnarLedger.vue"),
    ("frontend/src/views/general-ledger/DetailLedger.vue", "ImgyWdCwBPuw", "DetailLedger.vue"),
    ("frontend/src/views/general-ledger/GeneralLedger.vue", "ImgyWdCwBPuw", "GeneralLedger.vue"),
    ("frontend/src/views/general-ledger/OriginalVoucher.vue", "ImgyWdCwBPuw", "OriginalVoucher.vue"),
    ("frontend/src/views/general-ledger/ProjectBalanceSheet.vue", "ImgyWdCwBPuw", "ProjectBalanceSheet.vue"),
    ("frontend/src/views/general-ledger/ProjectDetailLedger.vue", "ImgyWdCwBPuw", "ProjectDetailLedger.vue"),
    ("frontend/src/views/general-ledger/QtyFxBalanceSheet.vue", "ImgyWdCwBPuw", "QtyFxBalanceSheet.vue"),
    ("frontend/src/views/general-ledger/QtyFxDetaiLedger.vue", "ImgyWdCwBPuw", "QtyFxDetaiLedger.vue"),
    ("frontend/src/views/general-ledger/VoucherList.vue", "ImgyWdCwBPuw", "VoucherList.vue"),
    ("frontend/src/views/general-ledger/Voucher.vue", "ImgyWdCwBPuw", "Voucher.vue"),
    # frontend/src/views/settings -> ISUCKYFBxcLd
    ("frontend/src/views/settings/Account.vue", "ISUCKYFBxcLd", "Account.vue"),
]

def get_file_size(path):
    return os.path.getsize(path)

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    total = len(FILES)
    success = 0
    failed = []
    
    for i, (rel_path, dir_id, file_name) in enumerate(FILES):
        full_path = os.path.join(BASE_DIR, rel_path)
        size = get_file_size(full_path)
        
        print(f"[{i+1}/{total}] {rel_path} ({size} bytes)", flush=True)
        
        # Write the three-step upload process to a temp script
        # We'll just print the instructions for the AI to execute
        print(f"  FILE_UPLOAD: dir_id={dir_id}, file_name={file_name}, file_size={size}, conflict_strategy=overwrite", flush=True)
        print(f"  CURL: -T {full_path}", flush=True)
        print(f"  FILE_UPLOAD_COMPLETE: dir_id={dir_id}, file_name={file_name}, file_size={size}", flush=True)
        print("---", flush=True)
    
    print(f"\nTotal files to upload: {total}", flush=True)

if __name__ == "__main__":
    main()
