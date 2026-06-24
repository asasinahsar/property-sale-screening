# 3レイヤードアーキテクチャガイド

## 構成図

```
┌──────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                      │
│  ────────────────────────────────────────────────────── │
│  - React Components (pages/, components/)               │
│  - TanStack Query hooks                                 │
│  - 入力バリデーション（ユーザーへの即座フィードバック） │
│  - UI状態管理（ローカル状態のみ）                       │
│  └─ 責務：「ユーザーと対話する」                        │
└────────────────────┬─────────────────────────────────────┘
                     │ 呼び出し
                     ▼
┌──────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER                                    │
│  ────────────────────────────────────────────────────── │
│  - Service / UseCase クラス                             │
│  - ビジネスルール、ドメインロジック                      │
│  - バリデーション（ビジネスレベル）                      │
│  - エラーハンドリング                                    │
│  - トランザクション管理                                  │
│  └─ 責務：「ビジネスルールを実装する」                  │
└────────────────────┬─────────────────────────────────────┘
                     │ 呼び出し
                     ▼
┌──────────────────────────────────────────────────────────┐
│  DATA ACCESS LAYER                                       │
│  ────────────────────────────────────────────────────── │
│  - Repository クラス                                    │
│  - データベースクエリ構築                                │
│  - ORM / ドライバー操作                                 │
│  - キャッシュ管理                                        │
│  └─ 責務：「データを永続化・取得する」                  │
└──────────────────────────────────────────────────────────┘
```

## 各レイヤーの詳細

### 1. Presentation Layer（プレゼンテーション層）

**責務**：ユーザーインタフェースとのやり取り

**含まれるもの**：
```typescript
// React Component
export function TaskCreateForm() {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Presentation層での即座なバリデーション
    if (!title.trim()) {
      setError("タイトルは必須です");
      return;
    }

    // Business Logic層を呼び出す
    await createTask(title);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={title} onChange={(e) => setTitle(e.target.value)} />
      {error && <span>{error}</span>}
      <button type="submit">作成</button>
    </form>
  );
}
```

**含まれないもの**：
- ❌ データベースアクセス
- ❌ 複雑なビジネスロジック

### 2. Business Logic Layer（ビジネスロジック層）

**責務**：ビジネスルール、ドメインロジックの実装

**含まれるもの**：
```typescript
// Service / UseCase
export class CreateTaskService {
  constructor(private taskRepository: TaskRepository) {}

  async execute(title: string): Promise<Task> {
    // ビジネスレベルのバリデーション
    if (title.length > 100) {
      throw new ValidationError("タイトルは100文字以内");
    }

    // 重複チェック（ビジネスルール）
    const existing = await this.taskRepository.findByTitle(title);
    if (existing) {
      throw new DuplicateTaskError("同じタイトルのタスクが存在します");
    }

    // Data Access層を呼び出す
    const task = await this.taskRepository.create({
      title,
      createdAt: new Date(),
      status: "pending"
    });

    // ビジネスロジック後処理（通知など）
    await this.notifyNewTask(task);

    return task;
  }

  private async notifyNewTask(task: Task): Promise<void> {
    // 通知処理
  }
}
```

**含まれないもの**：
- ❌ HTTP レスポンス
- ❌ SQL クエリ

### 3. Data Access Layer（データアクセス層）

**責務**：データベースへのアクセス、永続化

**含まれるもの**：
```typescript
// Repository
export class TaskRepository {
  constructor(private db: Database) {}

  async create(data: {
    title: string;
    createdAt: Date;
    status: string;
  }): Promise<Task> {
    // SQL クエリ構築（またはORM操作）
    const result = await this.db.insert("tasks").values({
      title: data.title,
      created_at: data.createdAt,
      status: data.status
    });

    return {
      id: result.lastID,
      ...data
    };
  }

  async findByTitle(title: string): Promise<Task | null> {
    const result = await this.db
      .select("*")
      .from("tasks")
      .where("title = ?", [title])
      .first();

    return result || null;
  }
}
```

**含まれないもの**：
- ❌ ビジネスルール
- ❌ エラーハンドリング（データベース固有の例外のみ変換）

## レイヤー間の通信

### Presentation → Business Logic（呼び出し）
```typescript
// pages/tasks/create.tsx
const service = new CreateTaskService(taskRepository);
const newTask = await service.execute(title);
```

### Business Logic → Data Access（呼び出し）
```typescript
// services/CreateTaskService.ts
const task = await this.taskRepository.create({...});
```

### 逆方向の依存は禁止
```typescript
// ❌ NG: Business Logic層が Presentation層に依存
// ❌ NG: Data Access層が Business Logic層に依存
```

## テストとの関連

各レイヤーは独立してテスト可能：

```typescript
// Data Access層のテスト
describe("TaskRepository", () => {
  it("should create a task", async () => {
    const repo = new TaskRepository(mockDB);
    const task = await repo.create({...});
    expect(task.id).toBeDefined();
  });
});

// Business Logic層のテスト
describe("CreateTaskService", () => {
  it("should throw on duplicate title", async () => {
    const mockRepo = new MockTaskRepository();
    const service = new CreateTaskService(mockRepo);

    await expect(service.execute("duplicate"))
      .rejects.toThrow(DuplicateTaskError);
  });
});

// Presentation層のテスト
describe("TaskCreateForm", () => {
  it("should show error on empty title", () => {
    render(<TaskCreateForm />);
    fireEvent.click(screen.getByText("作成"));
    expect(screen.getByText("タイトルは必須です")).toBeInTheDocument();
  });
});
```

## チェックリスト

実装時に以下を確認：

- [ ] Presentation層は UI と入力受け付けのみ
- [ ] Business Logic層は ビジネスルールのみ
- [ ] Data Access層は データベース操作のみ
- [ ] 逆方向の依存がない
- [ ] 各レイヤーが独立してテスト可能
