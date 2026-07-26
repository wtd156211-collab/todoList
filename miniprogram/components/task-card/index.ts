if (typeof Component !== 'undefined') {
  Component({
    properties: {
      title: { type: String, value: '' },
      dueText: { type: String, value: '' },
      priority: { type: String, value: 'medium' }
    }
  });
}
