import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  CheckCircleFilled,
  CloudUploadOutlined,
  CloseCircleFilled,
  DashboardOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  SyncOutlined,
  TeamOutlined,
  UserOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  ConfigProvider,
  Descriptions,
  Empty,
  Form,
  Input,
  Layout,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  Upload,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { UploadProps } from "antd";
import zhCN from "antd/locale/zh_CN";
import "./styles.css";

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

type Entry = "ops" | "portal";
type ImportTaskStatus = "pending" | "processing" | "completed" | "failed";

type ImportTask = {
  id: string;
  filename: string;
  status: ImportTaskStatus;
  total_rows: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

type UserRole = "platform_admin" | "business_admin" | "salesperson";

type AppUser = {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  role_name: string;
  status: string;
  permissions: string[];
  ops_menus: string[];
  portal_menus: string[];
};

type RoleDefinition = {
  role: UserRole;
  name: string;
  description: string;
  permissions: string[];
  ops_menus: string[];
  portal_menus: string[];
};

type LoginResponse = {
  request_id: string;
  token: string;
  user: AppUser;
};

type ListResponse<T> = {
  request_id: string;
  items: T[];
};

type ItemResponse<T> = {
  request_id: string;
  item: T;
};

const menuIconMap: Record<string, React.ReactNode> = {
  数据上传: <CloudUploadOutlined />,
  导入任务: <DatabaseOutlined />,
  数据异常处理: <WarningOutlined />,
  用户账号管理: <TeamOutlined />,
  角色权限设置: <SafetyCertificateOutlined />,
  数据查询: <FileSearchOutlined />,
  数据看板: <DashboardOutlined />,
};

function createRequestId() {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function currentEntry(): Entry | undefined {
  if (window.location.pathname.startsWith("/ops")) {
    return "ops";
  }
  if (window.location.pathname.startsWith("/portal")) {
    return "portal";
  }
  return undefined;
}

function statusIcon(task: ImportTask) {
  if (task.status === "completed") {
    return (
      <Tooltip title="解析正常">
        <CheckCircleFilled className="status-icon status-icon-success" />
      </Tooltip>
    );
  }

  if (task.status === "failed") {
    return (
      <Tooltip title={task.error_message || "解析异常"}>
        <CloseCircleFilled className="status-icon status-icon-error" />
      </Tooltip>
    );
  }

  return (
    <Tooltip title="解析中">
      <SyncOutlined spin className="status-icon status-icon-processing" />
    </Tooltip>
  );
}

function useSession(entry: Entry) {
  const [token, setToken] = useState(() => localStorage.getItem(`medical-data-${entry}-token`) || "");
  const [user, setUser] = useState<AppUser | null>(() => {
    const raw = localStorage.getItem(`medical-data-${entry}-user`);
    return raw ? (JSON.parse(raw) as AppUser) : null;
  });

  function save(nextToken: string, nextUser: AppUser) {
    localStorage.setItem(`medical-data-${entry}-token`, nextToken);
    localStorage.setItem(`medical-data-${entry}-user`, JSON.stringify(nextUser));
    setToken(nextToken);
    setUser(nextUser);
  }

  function clear() {
    localStorage.removeItem(`medical-data-${entry}-token`);
    localStorage.removeItem(`medical-data-${entry}-user`);
    setToken("");
    setUser(null);
  }

  return { token, user, save, clear };
}

function authHeaders(token: string, user?: AppUser | null) {
  return {
    Authorization: `Bearer ${token}`,
    "X-Request-ID": createRequestId(),
    "X-User-ID": user?.id || "anonymous",
  };
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload as T;
}

function Gateway() {
  return (
    <ConfigProvider locale={zhCN}>
      <Layout className="app-shell">
        <Header className="app-header">
          <div>
            <Title level={4}>药品流向数据平台</Title>
            <Text>请选择工作入口</Text>
          </div>
          <Tag color="processing">ops / portal</Tag>
        </Header>
        <Content className="app-content">
          <div className="entry-grid">
            <Card title="运营端" className="entry-card">
              <Paragraph>面向平台管理员、数据维护人员和业务员，用于上传数据、查看导入任务、处理异常、管理账号和角色权限。</Paragraph>
              <Button type="primary" href="/ops">
                进入运营端
              </Button>
            </Card>
            <Card title="用户端" className="entry-card">
              <Paragraph>面向业务老板、业务管理员和业务员，登录后按角色权限展示数据查询和数据看板菜单。</Paragraph>
              <Button href="/portal">进入用户端</Button>
            </Card>
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

function LoginCard({ entry, onLogin }: { entry: Entry; onLogin: (token: string, user: AppUser) => void }) {
  const [loading, setLoading] = useState(false);

  async function submit(values: { username: string; password: string }) {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": createRequestId(),
          "X-User-ID": values.username,
        },
        body: JSON.stringify({ ...values, entry }),
      });
      const payload = await parseResponse<LoginResponse>(response);
      onLogin(payload.token, payload.user);
      message.success("登录成功");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ConfigProvider locale={zhCN}>
      <Layout className="app-shell">
        <Header className="app-header">
          <div>
            <Title level={4}>药品流向数据平台</Title>
            <Text>{entry === "ops" ? "运营端登录" : "用户端登录"}</Text>
          </div>
          <Button href="/">返回入口</Button>
        </Header>
        <Content className="login-content">
          <Card className="login-card" title={entry === "ops" ? "运营端" : "用户端"}>
            <Form layout="vertical" onFinish={submit} initialValues={{ username: "admin", password: "admin123" }}>
              <Form.Item label="账号" name="username" rules={[{ required: true, message: "请输入账号" }]}>
                <Input prefix={<UserOutlined />} />
              </Form.Item>
              <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}>
                <Input.Password />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                登录
              </Button>
            </Form>
            <Alert
              className="login-hint"
              type="info"
              showIcon
              message="默认账号：admin/admin123，manager/manager123，sales/sales123"
            />
          </Card>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

function OpsApp() {
  const session = useSession("ops");
  const [selectedMenu, setSelectedMenu] = useState("数据上传");

  if (!session.token || !session.user) {
    return <LoginCard entry="ops" onLogin={session.save} />;
  }

  const menuItems = session.user.ops_menus.map((label) => ({
    key: label,
    icon: menuIconMap[label],
    label,
  }));

  return (
    <ConfigProvider locale={zhCN}>
      <Layout className="app-shell">
        <Sider className="app-sider" width={224}>
          <Title level={4}>运营端</Title>
          <SideNav items={menuItems} selectedKey={selectedMenu} onSelect={setSelectedMenu} />
        </Sider>
        <Layout>
          <Header className="app-header">
            <div>
              <Title level={4}>药品流向数据平台</Title>
              <Text>
                {session.user.display_name} · {session.user.role_name}
              </Text>
            </div>
            <Space>
              <Button href="/portal">用户端</Button>
              <Button onClick={session.clear}>退出</Button>
            </Space>
          </Header>
          <Content className="app-content">
            <OpsContent menu={selectedMenu} token={session.token} user={session.user} />
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

function OpsContent({ menu, token, user }: { menu: string; token: string; user: AppUser }) {
  if (menu === "数据上传") {
    return <ImportWorkspace token={token} user={user} mode="upload" />;
  }
  if (menu === "导入任务") {
    return <ImportWorkspace token={token} user={user} mode="tasks" />;
  }
  if (menu === "数据异常处理") {
    return <ImportWorkspace token={token} user={user} mode="exceptions" />;
  }
  if (menu === "用户账号管理") {
    return <UserManagement token={token} user={user} />;
  }
  if (menu === "角色权限设置") {
    return <RoleSettings token={token} user={user} />;
  }
  return <Empty description="当前角色没有可用功能" />;
}

function ImportWorkspace({ token, user, mode }: { token: string; user: AppUser; mode: "upload" | "tasks" | "exceptions" }) {
  const [tasks, setTasks] = useState<ImportTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [lastRequestId, setLastRequestId] = useState<string>();
  const [apiError, setApiError] = useState<string>();

  async function loadTasks() {
    setLoading(true);
    setApiError(undefined);
    try {
      const response = await fetch(`${API_BASE_URL}/import-tasks`, {
        headers: authHeaders(token, user),
      });
      const payload = await parseResponse<ListResponse<ImportTask>>(response);
      setTasks(payload.items);
      setLastRequestId(payload.request_id);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "任务列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  const uploadFile: UploadProps["customRequest"] = async (options) => {
    const file = options.file as File;
    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setApiError(undefined);
    try {
      const response = await fetch(`${API_BASE_URL}/import-tasks`, {
        method: "POST",
        headers: authHeaders(token, user),
        body: formData,
      });
      const payload = await parseResponse<ItemResponse<ImportTask>>(response);
      setLastRequestId(payload.request_id);
      setTasks((current) => [payload.item, ...current.filter((item) => item.id !== payload.item.id)]);
      options.onSuccess?.(payload);
      message.success("上传完成，已创建解析任务");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "文件上传失败";
      setApiError(errorMessage);
      options.onError?.(new Error(errorMessage));
      message.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    void loadTasks();
  }, []);

  const visibleTasks = mode === "exceptions" ? tasks.filter((task) => task.status === "failed") : tasks;

  return (
    <Space direction="vertical" size={20} className="full-width">
      <section className="overview">
        <Title level={2}>{mode === "exceptions" ? "数据异常处理" : mode === "tasks" ? "导入任务状态" : "数据上传"}</Title>
        <Text>支持 Excel 和 CSV。每次上传都会创建唯一导入编号，并记录 requestID 方便审计追踪。</Text>
      </section>
      {mode === "upload" ? (
        <Card className="upload-panel" title="上传文件">
          <Dragger accept=".csv,.xls,.xlsx" customRequest={uploadFile} disabled={uploading} maxCount={1} showUploadList={false}>
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽上传 Excel / CSV</p>
            <p className="ant-upload-hint">上传后会立即创建解析任务并显示结果状态。</p>
          </Dragger>
        </Card>
      ) : null}
      <Card title={mode === "exceptions" ? "异常任务" : "解析任务"}>
        <Space direction="vertical" size={12} className="full-width">
          <Space>
            <Button icon={<DatabaseOutlined />} loading={loading} onClick={() => void loadTasks()}>
              刷新任务列表
            </Button>
            {lastRequestId ? <Tag color="blue">最近 requestID：{lastRequestId}</Tag> : null}
          </Space>
          {apiError ? <Alert type="error" showIcon message={apiError} /> : null}
          <ImportTaskTable tasks={visibleTasks} loading={loading} />
        </Space>
      </Card>
    </Space>
  );
}

function ImportTaskTable({ tasks, loading }: { tasks: ImportTask[]; loading: boolean }) {
  const columns: ColumnsType<ImportTask> = [
    {
      title: "状态",
      dataIndex: "status",
      width: 100,
      render: (_value, task) => (
        <Space size={8}>
          {statusIcon(task)}
          <Text>{task.status === "completed" ? "正常" : task.status === "failed" ? "异常" : "解析中"}</Text>
        </Space>
      ),
    },
    { title: "导入编号", dataIndex: "id", ellipsis: true },
    { title: "文件名", dataIndex: "filename", ellipsis: true },
    { title: "行数", dataIndex: "total_rows", width: 90, align: "right" },
    { title: "创建时间", dataIndex: "created_at", width: 220 },
  ];

  return <Table columns={columns} dataSource={tasks} loading={loading} pagination={{ pageSize: 8 }} rowKey="id" />;
}

function UserManagement({ token, user }: { token: string; user: AppUser }) {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [roles, setRoles] = useState<RoleDefinition[]>([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  async function loadData() {
    setLoading(true);
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/users`, { headers: authHeaders(token, user) }),
        fetch(`${API_BASE_URL}/auth/roles`, { headers: authHeaders(token, user) }),
      ]);
      setUsers((await parseResponse<ListResponse<AppUser>>(usersResponse)).items);
      setRoles((await parseResponse<ListResponse<RoleDefinition>>(rolesResponse)).items);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "账号数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function createAccount(values: { username: string; display_name: string; password: string; role: UserRole }) {
    try {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: {
          ...authHeaders(token, user),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(values),
      });
      const payload = await parseResponse<ItemResponse<AppUser>>(response);
      setUsers((current) => [payload.item, ...current]);
      form.resetFields();
      message.success("账号已创建");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "账号创建失败");
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <div className="management-grid">
      <Card title="创建用户账号">
        <Form form={form} layout="vertical" onFinish={createAccount}>
          <Form.Item label="账号" name="username" rules={[{ required: true, message: "请输入账号" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="姓名" name="display_name" rules={[{ required: true, message: "请输入姓名" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="初始密码" name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item label="角色" name="role" rules={[{ required: true, message: "请选择角色" }]}>
            <Select options={roles.map((role) => ({ value: role.role, label: role.name }))} />
          </Form.Item>
          <Button type="primary" htmlType="submit">
            创建账号
          </Button>
        </Form>
      </Card>
      <Card title="用户账号列表">
        <Table
          loading={loading}
          rowKey="id"
          dataSource={users}
          columns={[
            { title: "账号", dataIndex: "username" },
            { title: "姓名", dataIndex: "display_name" },
            { title: "角色", dataIndex: "role_name" },
            { title: "状态", dataIndex: "status", render: (status) => <Tag color="green">{status}</Tag> },
          ]}
        />
      </Card>
    </div>
  );
}

function RoleSettings({ token, user }: { token: string; user: AppUser }) {
  const [roles, setRoles] = useState<RoleDefinition[]>([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/roles`, { headers: authHeaders(token, user) })
      .then((response) => parseResponse<ListResponse<RoleDefinition>>(response))
      .then((payload) => setRoles(payload.items))
      .catch((error) => message.error(error instanceof Error ? error.message : "角色加载失败"));
  }, []);

  return (
    <Card title="角色权限设置">
      <Table
        rowKey="role"
        dataSource={roles}
        columns={[
          { title: "角色", dataIndex: "name", width: 150 },
          { title: "说明", dataIndex: "description" },
          { title: "运营端菜单", dataIndex: "ops_menus", render: (menus: string[]) => menus.map((menu) => <Tag key={menu}>{menu}</Tag>) },
          { title: "用户端菜单", dataIndex: "portal_menus", render: (menus: string[]) => menus.map((menu) => <Tag key={menu}>{menu}</Tag>) },
        ]}
      />
    </Card>
  );
}

function PortalApp() {
  const session = useSession("portal");
  const [selectedMenu, setSelectedMenu] = useState("数据查询");

  if (!session.token || !session.user) {
    return <LoginCard entry="portal" onLogin={session.save} />;
  }

  const availableMenus = session.user.portal_menus;
  const selected = availableMenus.includes(selectedMenu) ? selectedMenu : availableMenus[0];

  return (
    <ConfigProvider locale={zhCN}>
      <Layout className="app-shell">
        <Sider className="app-sider" width={224}>
          <Title level={4}>用户端</Title>
          <SideNav
            items={availableMenus.map((label) => ({ key: label, icon: menuIconMap[label], label }))}
            selectedKey={selected}
            onSelect={setSelectedMenu}
          />
        </Sider>
        <Layout>
          <Header className="app-header">
            <div>
              <Title level={4}>药品流向数据平台</Title>
              <Text>
                {session.user.display_name} · {session.user.role_name}
              </Text>
            </div>
            <Space>
              <Button href="/ops">运营端</Button>
              <Button onClick={session.clear}>退出</Button>
            </Space>
          </Header>
          <Content className="app-content">
            {selected === "数据看板" ? <DashboardView /> : <DataQueryView user={session.user} />}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

function DataQueryView({ user }: { user: AppUser }) {
  return (
    <Space direction="vertical" size={20} className="full-width">
      <section className="overview">
        <Title level={2}>数据查询</Title>
        <Text>当前只搭建查询入口和权限展示，真实业务字段会在拿到数据样本后补齐。</Text>
      </section>
      <Card>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="当前账号">{user.username}</Descriptions.Item>
          <Descriptions.Item label="角色">{user.role_name}</Descriptions.Item>
          <Descriptions.Item label="可用菜单">{user.portal_menus.map((menu) => <Tag key={menu}>{menu}</Tag>)}</Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  );
}

function DashboardView() {
  return (
    <Space direction="vertical" size={20} className="full-width">
      <section className="overview">
        <Title level={2}>数据看板</Title>
        <Text>当前看板先展示占位指标，后续接入真实流向数据后替换为图表。</Text>
      </section>
      <div className="dashboard-grid">
        <Card>
          <Statistic title="今日导入任务" value={0} />
        </Card>
        <Card>
          <Statistic title="待处理异常" value={0} />
        </Card>
        <Card>
          <Statistic title="可查询数据集" value={0} />
        </Card>
      </div>
    </Space>
  );
}

function App() {
  const entry = currentEntry();
  if (entry === "ops") {
    return <OpsApp />;
  }
  if (entry === "portal") {
    return <PortalApp />;
  }
  return <Gateway />;
}

function SideNav({
  items,
  selectedKey,
  onSelect,
}: {
  items: Array<{ key: string; icon: React.ReactNode; label: string }>;
  selectedKey: string;
  onSelect: (key: string) => void;
}) {
  return (
    <nav className="side-nav">
      {items.map((item) => (
        <button
          className={item.key === selectedKey ? "side-nav-item side-nav-item-active" : "side-nav-item"}
          key={item.key}
          onClick={() => onSelect(item.key)}
          type="button"
        >
          <span className="side-nav-icon">{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
