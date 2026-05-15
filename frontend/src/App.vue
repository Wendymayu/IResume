<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
        <h1 class="text-xl font-bold text-indigo-600">IResume</h1>
        <router-link to="/profile" class="text-gray-600 hover:text-indigo-600" active-class="text-indigo-600 font-medium">
          个人档案
        </router-link>
        <router-link to="/resume" class="text-gray-600 hover:text-indigo-600" active-class="text-indigo-600 font-medium">
          生成简历
        </router-link>
      </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>
