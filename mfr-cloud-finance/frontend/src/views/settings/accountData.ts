export interface AccountItem {
  id: string
  code: string
  name: string
  category: string
  unit?: string
  direction: '借' | '贷'
  auxCalc?: string
  foreignCurrency?: string
  children?: AccountItem[]
  level: number
  expanded?: boolean
}

export const accountData: Record<string, AccountItem[]> = {
  "asset": [
    {
      "id": "1001",
      "code": "1001",
      "name": "库存现金",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1002",
      "code": "1002",
      "name": "银行存款",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1012",
      "code": "1012",
      "name": "其他货币资金",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1101",
      "code": "1101",
      "name": "短期投资",
      "category": "资产",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "1101001",
          "code": "1101001",
          "name": "股票",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1101002",
          "code": "1101002",
          "name": "债券",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1101003",
          "code": "1101003",
          "name": "基金",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1101010",
          "code": "1101010",
          "name": "其他",
          "category": "资产",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "1121",
      "code": "1121",
      "name": "应收票据",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1122",
      "code": "1122",
      "name": "应收账款",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1123",
      "code": "1123",
      "name": "预付账款",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1131",
      "code": "1131",
      "name": "应收股利",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1132",
      "code": "1132",
      "name": "应收利息",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1221",
      "code": "1221",
      "name": "其他应收款",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1401",
      "code": "1401",
      "name": "材料采购",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1402",
      "code": "1402",
      "name": "在途物资",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1403",
      "code": "1403",
      "name": "原材料",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1404",
      "code": "1404",
      "name": "材料成本差异",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1405",
      "code": "1405",
      "name": "库存商品",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1407",
      "code": "1407",
      "name": "商品进销差价",
      "category": "资产",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "1408",
      "code": "1408",
      "name": "委托加工物资",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1411",
      "code": "1411",
      "name": "周转材料",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1421",
      "code": "1421",
      "name": "消耗性生物资产",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1501",
      "code": "1501",
      "name": "长期债券投资",
      "category": "资产",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "1501001",
          "code": "1501001",
          "name": "债券投资",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1501002",
          "code": "1501002",
          "name": "其他债券投资",
          "category": "资产",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "1511",
      "code": "1511",
      "name": "长期股权投资",
      "category": "资产",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "1511001",
          "code": "1511001",
          "name": "股票投资",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1511002",
          "code": "1511002",
          "name": "其他股权投资",
          "category": "资产",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "1601",
      "code": "1601",
      "name": "固定资产",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1602",
      "code": "1602",
      "name": "累计折旧",
      "category": "资产",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "1604",
      "code": "1604",
      "name": "在建工程",
      "category": "资产",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "1604001",
          "code": "1604001",
          "name": "建筑工程",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1604002",
          "code": "1604002",
          "name": "安装工程",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1604003",
          "code": "1604003",
          "name": "技术改造工程",
          "category": "资产",
          "direction": "借",
          "level": 2
        },
        {
          "id": "1604004",
          "code": "1604004",
          "name": "其他支出",
          "category": "资产",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "1605",
      "code": "1605",
      "name": "工程物资",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1606",
      "code": "1606",
      "name": "固定资产清理",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1621",
      "code": "1621",
      "name": "生产性生物资产",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1622",
      "code": "1622",
      "name": "生产性生物资产累计折旧",
      "category": "资产",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "1701",
      "code": "1701",
      "name": "无形资产",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1702",
      "code": "1702",
      "name": "累计摊销",
      "category": "资产",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "1801",
      "code": "1801",
      "name": "长期待摊费用",
      "category": "资产",
      "direction": "借",
      "level": 1
    },
    {
      "id": "1901",
      "code": "1901",
      "name": "待处理财产损溢",
      "category": "资产",
      "direction": "借",
      "level": 1
    }
  ],
  "liability": [
    {
      "id": "2001",
      "code": "2001",
      "name": "短期借款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2201",
      "code": "2201",
      "name": "应付票据",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2202",
      "code": "2202",
      "name": "应付账款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2203",
      "code": "2203",
      "name": "预收账款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2211",
      "code": "2211",
      "name": "应付职工薪酬",
      "category": "负债",
      "direction": "贷",
      "level": 1,
      "children": [
        {
          "id": "2211001",
          "code": "2211001",
          "name": "应付职工工资",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211002",
          "code": "2211002",
          "name": "应付奖金、津贴和补贴",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211003",
          "code": "2211003",
          "name": "应付福利费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211004",
          "code": "2211004",
          "name": "应付社会保险费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211005",
          "code": "2211005",
          "name": "应付住房公积金",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211006",
          "code": "2211006",
          "name": "应付工会经费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211007",
          "code": "2211007",
          "name": "应付教育经费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211008",
          "code": "2211008",
          "name": "非货币性福利",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211009",
          "code": "2211009",
          "name": "辞退福利",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2211010",
          "code": "2211010",
          "name": "其他应付职工薪酬",
          "category": "负债",
          "direction": "贷",
          "level": 2
        }
      ]
    },
    {
      "id": "2221",
      "code": "2221",
      "name": "应交税费",
      "category": "负债",
      "direction": "贷",
      "level": 1,
      "children": [
        {
          "id": "2221001",
          "code": "2221001",
          "name": "应交增值税",
          "category": "负债",
          "direction": "贷",
          "level": 2,
          "children": [
            {
              "id": "2221001001",
              "code": "2221001001",
              "name": "进项税额",
              "category": "负债",
              "direction": "借",
              "level": 3
            },
            {
              "id": "2221001002",
              "code": "2221001002",
              "name": "已交税金",
              "category": "负债",
              "direction": "借",
              "level": 3
            },
            {
              "id": "2221001003",
              "code": "2221001003",
              "name": "转出未交增值税",
              "category": "负债",
              "direction": "借",
              "level": 3
            },
            {
              "id": "2221001004",
              "code": "2221001004",
              "name": "减免税款",
              "category": "负债",
              "direction": "借",
              "level": 3
            },
            {
              "id": "2221001005",
              "code": "2221001005",
              "name": "销项税额",
              "category": "负债",
              "direction": "贷",
              "level": 3
            },
            {
              "id": "2221001006",
              "code": "2221001006",
              "name": "出口退税",
              "category": "负债",
              "direction": "贷",
              "level": 3
            },
            {
              "id": "2221001007",
              "code": "2221001007",
              "name": "进项税额转出",
              "category": "负债",
              "direction": "贷",
              "level": 3
            },
            {
              "id": "2221001008",
              "code": "2221001008",
              "name": "出口抵减内销产品应纳税额",
              "category": "负债",
              "direction": "借",
              "level": 3
            },
            {
              "id": "2221001009",
              "code": "2221001009",
              "name": "移出多交增值税",
              "category": "负债",
              "direction": "贷",
              "level": 3
            },
            {
              "id": "2221001010",
              "code": "2221001010",
              "name": "销项税额抵减",
              "category": "负债",
              "direction": "借",
              "level": 3
            }
          ]
        },
        {
          "id": "2221002",
          "code": "2221002",
          "name": "未交增值税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221003",
          "code": "2221003",
          "name": "应交营业税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221004",
          "code": "2221004",
          "name": "应交消费税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221005",
          "code": "2221005",
          "name": "应交资源税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221006",
          "code": "2221006",
          "name": "应交企业所得税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221007",
          "code": "2221007",
          "name": "应交土地增值税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221008",
          "code": "2221008",
          "name": "应交城市维护建设税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221009",
          "code": "2221009",
          "name": "应交房产税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221010",
          "code": "2221010",
          "name": "应交城镇土地使用税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221011",
          "code": "2221011",
          "name": "应交车船使用税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221012",
          "code": "2221012",
          "name": "应交个人所得税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221013",
          "code": "2221013",
          "name": "教育费附加",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221014",
          "code": "2221014",
          "name": "矿产资源补偿费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221015",
          "code": "2221015",
          "name": "排污费",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221016",
          "code": "2221016",
          "name": "印花税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221017",
          "code": "2221017",
          "name": "地方教育费附加",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221018",
          "code": "2221018",
          "name": "地方水利建设基金",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221019",
          "code": "2221019",
          "name": "预交增值税",
          "category": "负债",
          "direction": "借",
          "level": 2
        },
        {
          "id": "2221020",
          "code": "2221020",
          "name": "待抵扣进项税",
          "category": "负债",
          "direction": "借",
          "level": 2
        },
        {
          "id": "2221021",
          "code": "2221021",
          "name": "待认证进项税",
          "category": "负债",
          "direction": "借",
          "level": 2
        },
        {
          "id": "2221022",
          "code": "2221022",
          "name": "待转销项税额",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221023",
          "code": "2221023",
          "name": "简易计税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221024",
          "code": "2221024",
          "name": "转让金融商品应交增值税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "2221025",
          "code": "2221025",
          "name": "代扣代交增值税",
          "category": "负债",
          "direction": "贷",
          "level": 2
        }
      ]
    },
    {
      "id": "2231",
      "code": "2231",
      "name": "应付利息",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2232",
      "code": "2232",
      "name": "应付利润",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2241",
      "code": "2241",
      "name": "其他应付款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2401",
      "code": "2401",
      "name": "递延收益",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2501",
      "code": "2501",
      "name": "长期借款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "2701",
      "code": "2701",
      "name": "长期应付款",
      "category": "负债",
      "direction": "贷",
      "level": 1
    }
  ],
  "equity": [
    {
      "id": "3001",
      "code": "3001",
      "name": "实收资本",
      "category": "权益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "3002",
      "code": "3002",
      "name": "资本公积",
      "category": "权益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "3101",
      "code": "3101",
      "name": "盈余公积",
      "category": "权益",
      "direction": "贷",
      "level": 1,
      "children": [
        {
          "id": "3101001",
          "code": "3101001",
          "name": "法定盈余公积",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3101002",
          "code": "3101002",
          "name": "任意盈余公积",
          "category": "权益",
          "direction": "贷",
          "level": 2
        }
      ]
    },
    {
      "id": "3103",
      "code": "3103",
      "name": "本年利润",
      "category": "权益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "3104",
      "code": "3104",
      "name": "利润分配",
      "category": "权益",
      "direction": "贷",
      "level": 1,
      "children": [
        {
          "id": "3104001",
          "code": "3104001",
          "name": "其他转入",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104002",
          "code": "3104002",
          "name": "提取法定盈余公积",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104003",
          "code": "3104003",
          "name": "提取法定公益金",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104004",
          "code": "3104004",
          "name": "提取职工奖励及福利基金",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104009",
          "code": "3104009",
          "name": "提取任意盈余公积",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104010",
          "code": "3104010",
          "name": "应付利润",
          "category": "权益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "3104015",
          "code": "3104015",
          "name": "未分配利润",
          "category": "权益",
          "direction": "贷",
          "level": 2
        }
      ]
    }
  ],
  "cost": [
    {
      "id": "4001",
      "code": "4001",
      "name": "生产成本",
      "category": "成本",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "4001001",
          "code": "4001001",
          "name": "基本生产成本",
          "category": "成本",
          "direction": "借",
          "level": 2
        },
        {
          "id": "4001002",
          "code": "4001002",
          "name": "辅助生产成本",
          "category": "成本",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "4101",
      "code": "4101",
      "name": "制造费用",
      "category": "成本",
      "direction": "借",
      "level": 1
    },
    {
      "id": "4301",
      "code": "4301",
      "name": "研发支出",
      "category": "成本",
      "direction": "借",
      "level": 1
    },
    {
      "id": "4401",
      "code": "4401",
      "name": "工程施工",
      "category": "成本",
      "direction": "借",
      "level": 1
    },
    {
      "id": "4403",
      "code": "4403",
      "name": "机械作业",
      "category": "成本",
      "direction": "借",
      "level": 1
    }
  ],
  "pnl": [
    {
      "id": "5001",
      "code": "5001",
      "name": "主营业务收入",
      "category": "损益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "5051",
      "code": "5051",
      "name": "其他业务收入",
      "category": "损益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "5111",
      "code": "5111",
      "name": "投资收益",
      "category": "损益",
      "direction": "贷",
      "level": 1
    },
    {
      "id": "5301",
      "code": "5301",
      "name": "营业外收入",
      "category": "损益",
      "direction": "贷",
      "level": 1,
      "children": [
        {
          "id": "5301001",
          "code": "5301001",
          "name": "非流动资产处置净收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301002",
          "code": "5301002",
          "name": "政府补助",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301003",
          "code": "5301003",
          "name": "捐赠收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301004",
          "code": "5301004",
          "name": "盘盈收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301005",
          "code": "5301005",
          "name": "确实无法偿付的应付账款",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301006",
          "code": "5301006",
          "name": "以作坏账损失处理后又收回的应收账款",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301007",
          "code": "5301007",
          "name": "出租包装物和商品的租金收入",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301008",
          "code": "5301008",
          "name": "逾期未退包装物押金收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301009",
          "code": "5301009",
          "name": "汇兑收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        },
        {
          "id": "5301010",
          "code": "5301010",
          "name": "违约金收益",
          "category": "损益",
          "direction": "贷",
          "level": 2
        }
      ]
    },
    {
      "id": "5401",
      "code": "5401",
      "name": "主营业务成本",
      "category": "损益",
      "direction": "借",
      "level": 1
    },
    {
      "id": "5402",
      "code": "5402",
      "name": "其他业务成本",
      "category": "损益",
      "direction": "借",
      "level": 1
    },
    {
      "id": "5403",
      "code": "5403",
      "name": "税金及附加",
      "category": "损益",
      "direction": "借",
      "level": 1
    },
    {
      "id": "5601",
      "code": "5601",
      "name": "销售费用",
      "category": "损益",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "5601001",
          "code": "5601001",
          "name": "销售人员职工薪酬",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601002",
          "code": "5601002",
          "name": "商品维修费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601003",
          "code": "5601003",
          "name": "运输费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601004",
          "code": "5601004",
          "name": "装卸费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601005",
          "code": "5601005",
          "name": "包装费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601006",
          "code": "5601006",
          "name": "保险费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601007",
          "code": "5601007",
          "name": "广告费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601008",
          "code": "5601008",
          "name": "业务宣传费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601009",
          "code": "5601009",
          "name": "展览费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601010",
          "code": "5601010",
          "name": "运输合理损耗",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5601011",
          "code": "5601011",
          "name": "入库前挑选整理费",
          "category": "损益",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "5602",
      "code": "5602",
      "name": "管理费用",
      "category": "损益",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "5602001",
          "code": "5602001",
          "name": "管理人员职工薪酬",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602002",
          "code": "5602002",
          "name": "办公费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602003",
          "code": "5602003",
          "name": "业务招待费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602004",
          "code": "5602004",
          "name": "开办费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602005",
          "code": "5602005",
          "name": "修理费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602006",
          "code": "5602006",
          "name": "水电费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602007",
          "code": "5602007",
          "name": "差旅费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602008",
          "code": "5602008",
          "name": "周转材料摊销",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602009",
          "code": "5602009",
          "name": "固定资产折旧",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602010",
          "code": "5602010",
          "name": "无形资产摊销",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602011",
          "code": "5602011",
          "name": "长期待摊费用摊销",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602012",
          "code": "5602012",
          "name": "技术转让费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602013",
          "code": "5602013",
          "name": "财产保险费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602014",
          "code": "5602014",
          "name": "聘请中介机构费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602015",
          "code": "5602015",
          "name": "咨询费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602016",
          "code": "5602016",
          "name": "诉讼费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5602017",
          "code": "5602017",
          "name": "研究费用",
          "category": "损益",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "5603",
      "code": "5603",
      "name": "财务费用",
      "category": "损益",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "5603001",
          "code": "5603001",
          "name": "利息费用",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5603002",
          "code": "5603002",
          "name": "汇兑损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5603003",
          "code": "5603003",
          "name": "银行手续费",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5603004",
          "code": "5603004",
          "name": "现金折扣",
          "category": "损益",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "5711",
      "code": "5711",
      "name": "营业外支出",
      "category": "损益",
      "direction": "借",
      "level": 1,
      "children": [
        {
          "id": "5711001",
          "code": "5711001",
          "name": "非流动资产处置净损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711002",
          "code": "5711002",
          "name": "赞助支出",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711003",
          "code": "5711003",
          "name": "捐赠支出",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711004",
          "code": "5711004",
          "name": "盘亏损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711005",
          "code": "5711005",
          "name": "坏账损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711006",
          "code": "5711006",
          "name": "存货毁损报废损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711007",
          "code": "5711007",
          "name": "无法收回的长期债券投资损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711008",
          "code": "5711008",
          "name": "无法收回的长期股权投资损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711009",
          "code": "5711009",
          "name": "自然灾害等不可抗力因素造成的损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711010",
          "code": "5711010",
          "name": "税收滞纳金",
          "category": "损益",
          "direction": "借",
          "level": 2
        },
        {
          "id": "5711011",
          "code": "5711011",
          "name": "罚没损失",
          "category": "损益",
          "direction": "借",
          "level": 2
        }
      ]
    },
    {
      "id": "5801",
      "code": "5801",
      "name": "所得税费用",
      "category": "损益",
      "direction": "借",
      "level": 1
    }
  ]
}
