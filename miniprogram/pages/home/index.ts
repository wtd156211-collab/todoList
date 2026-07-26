Page({
  data: {
    greeting: '今天，专注完成一件重要的事',
    tasks: [] as Array<{ id: string; title: string; dueText: string; priority: string }>
  },
  onAddTask() {
    wx.navigateTo({ url: '/pages/task-form/index' });
  }
});
