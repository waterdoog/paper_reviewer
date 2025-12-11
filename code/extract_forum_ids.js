// 在浏览器控制台运行此脚本来提取所有 forum ID（仅提取ID，不包含表格数据）
// Run this script in browser console to extract all forum IDs (IDs only, no table data)
// 
// ⚠️  推荐使用 extract_table_data.js，它会同时提取 forum ID 和表格数据
// ⚠️  Recommended to use extract_table_data.js, which extracts both forum IDs and table data
//
// 使用方法：打开 https://agents4science.stanford.edu/submissions.html，按 F12 打开控制台，粘贴此脚本并运行
// Usage: Open https://agents4science.stanford.edu/submissions.html, press F12 to open console, paste this script and run

(function() {
    const links = Array.from(document.querySelectorAll('a[href*="openreview.net/forum"]'));
    const forumIds = links.map(a => {
        const match = a.href.match(/forum\?id=([^&]+)/);
        return match ? match[1] : null;
    }).filter(id => id);
    
    // 复制到剪贴板
    // Copy to clipboard
    const text = forumIds.join('\n');
    navigator.clipboard.writeText(text).then(() => {
        console.log(`✅ 已提取 ${forumIds.length} 个 forum ID 并复制到剪贴板`);
        console.log(`✅ Extracted ${forumIds.length} forum IDs and copied to clipboard`);
        console.log('📋 请将内容粘贴到 downloads/forum_ids.txt 文件中');
        console.log('📋 Please paste the content into downloads/forum_ids.txt file');
    }).catch(err => {
        console.log('⚠️  无法复制到剪贴板，请手动复制下面的内容');
        console.log('⚠️  Cannot copy to clipboard, please manually copy the content below:');
        console.log('\n' + text);
    });
    
    // 也输出到控制台
    // Also output to console
    console.log('\n所有 forum ID:');
    console.log('All forum IDs:');
    console.log(forumIds);
    
    return forumIds;
})();

