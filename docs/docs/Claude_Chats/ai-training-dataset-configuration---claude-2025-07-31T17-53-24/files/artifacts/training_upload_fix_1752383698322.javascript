// Replace the handleDataSourceNext() function in your training script with this fixed version:

async function handleDataSourceNext() {
    if (selectedDataSource === 'new_dataset') {
        // Create dataset first
        const name = prompt('Dataset name:', `${selectedModel}_dataset_${Date.now()}`);
        if (!name) return;

        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('model_type', selectedModel);
            formData.append('description', `Dataset for ${selectedModel} training`);

            const response = await fetch('/api/dataset/create', {
                method: 'POST',
                body: formData
            });

            const result = await response.json