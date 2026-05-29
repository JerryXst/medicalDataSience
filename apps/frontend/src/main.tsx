import React from "react";
import ReactDOM from "react-dom/client";
import { CloudDownloadOutlined, DatabaseOutlined, WarningOutlined } from "@ant-design/icons";
import { Card, Col, ConfigProvider, Layout, Row, Space, Tag, Typography } from "antd";
import zhCN from "antd/locale/zh_CN";
import "./styles.css";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const pipelineItems = [
  {
    icon: <CloudDownloadOutlined />,
    title: "RPA 采集",
    description: "每日自动下载重点商业平台原始文件，失败时保留人工补传入口。",
  },
  {
    icon: <DatabaseOutlined />,
    title: "清洗入库",
    description: "保存原始文件、创建导入批次，并将 Excel 转换为标准流向记录。",
  },
  {
    icon: <WarningOutlined />,
    title: "异常池",
    description: "客户、医院、产品无法确认时进入人工确认队列，确认后沉淀别名规则。",
  },
];

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Layout className="app-shell">
        <Header className="app-header">
          <div>
            <Title level={4}>药品流向数据平台</Title>
            <Text>V1 工程骨架</Text>
          </div>
          <Tag color="processing">Web-only MVP</Tag>
        </Header>
        <Content className="app-content">
          <section className="overview">
            <Title level={2}>核心业务流程</Title>
            <Text>
              第一版聚焦跑通每日采集、原始文件归档、数据清洗、异常处理和 Web 查询的最小闭环。
            </Text>
          </section>
          <Row gutter={[16, 16]}>
            {pipelineItems.map((item) => (
              <Col xs={24} md={8} key={item.title}>
                <Card className="pipeline-card">
                  <Space direction="vertical" size={12}>
                    <span className="pipeline-icon">{item.icon}</span>
                    <Title level={4}>{item.title}</Title>
                    <Text>{item.description}</Text>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
