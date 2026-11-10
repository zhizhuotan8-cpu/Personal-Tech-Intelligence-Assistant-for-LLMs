"""本地工程情报助手入口。"""
import argparse


def main():
    parser = argparse.ArgumentParser(description='个人大模型应用工程情报助手')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preview', action='store_true', help='重新生成真实简报（默认）')
    mode.add_argument('--demo', action='store_true', help='离线样本演示')
    mode.add_argument('--daily', action='store_true', help='每日运行，已完成则跳过')
    parser.add_argument('--days', type=int, default=7, help='动态信息回溯天数，默认七天')
    parser.add_argument('--no-open', action='store_true', help='不自动打开报告')
    parser.add_argument('--full-evidence', action='store_true', help='初选阶段也补正文')
    args = parser.parse_args()
    if args.days < 1:
        parser.error('--days 必须大于零')
    if args.daily:
        from trendradar.daily import run_daily
        return run_daily()
    from trendradar.preview import run_preview
    return run_preview(args.demo, args.no_open, args.full_evidence, args.days)


if __name__ == '__main__':
    raise SystemExit(main())
