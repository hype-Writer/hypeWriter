<script>
	let { children } = $props();

	let isLoggedIn = $state(false);
	let username = $state('');
</script>

<div class="app-container">
	<header>
		<nav>
			<div class="brand">
				<a href="/">HypeWriter</a>
			</div>

			<div class="nav-links">
				{#if isLoggedIn}
					<a href="/dashboard">Dashboard</a>
					<a href="/projects">Projects</a>
					<div class="user-menu">
						<span>{username}</span>
						<button
							onclick={() => {
								/* handle logout */
							}}>Logout</button
						>
					</div>
				{:else}
					<a href="/login">Login</a>
					<a href="/register">Register</a>
				{/if}
			</div>
		</nav>
	</header>

	{@render children()}

	<footer>
		<p>© 2025 HypeWriter</p>
	</footer>
</div>

<style>
	.app-container {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	header {
		padding: 1rem;
		background: #f8f9fa;
	}

	nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.nav-links {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	footer {
		margin-top: auto;
		padding: 1rem;
		text-align: center;
		background: #f8f9fa;
	}
</style>
