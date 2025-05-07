1. Svelte 5 Migration Guide (Selected Sections):**

*   **Reactivity Syntax Changes:**
    *   `let` -\> `$state()`:  Top-level `let` declarations are no longer implicitly reactive. Wrap the initial value with `$state()` to create reactive state.
    *   `$: ...` -\> `$derived()`/`$effect()`: Reactive statements are replaced by `$derived()` for derived values (computations) and `$effect()` for side effects.

    ```svelte
    <script>
    // Svelte 4
    let count = 0;
    $: doubled = count * 2;
    $: console.log("Count changed:", count);

    // Svelte 5
    let count = $state(0);
    let doubled = $derived(count * 2);
    $effect(() => {
        console.log("Count changed:", count);
    });
    </script>
    ```
    *   `export let` -\> `$props()`: Component properties are now declared using destructuring with `$props()`.

    ```svelte
    <script>
    // Svelte 4
    export let message = "";
    export let name;

    // Svelte 5
    let { message = "", name } = $props();
    </script>
    ```

*   **Event Changes:**
    *   `on:event={handler}` -\> `onevent={handler}`: The `on:` directive for event handling is replaced by event attributes.

    ```svelte
    <script>
    // Svelte 4
    function handleClick() {
        console.log("Clicked!");
    }

    // Svelte 5
    let onclick = () => {
        console.log("Clicked!");
    };
    </script>

    <button on:click={handleClick} onclick={onclick}>Click me</button>
    ```

*   **Snippets instead of Slots:**  Slots are replaced with snippets (`#snippet` and `@render`).

    ```svelte
    // Svelte 4
    <MyComponent>
        <div slot="header">Header Content</div>
        <p>Default Content</p>
    </MyComponent>

    // Svelte 5
    <MyComponent>
        {#snippet header()}
            <div>Header Content</div>
        {/snippet}
        <p>Default Content</p>
    </MyComponent>
    ```

    In `MyComponent.svelte`:

    ```svelte
    // Svelte 4
    <div>
        <slot name="header">Default Header</slot>
        <slot>Default Content</slot>
    </div>

    // Svelte 5
    <script>
      let { header, children } = $props();
    </script>
    <div>
        {@render header ? header() : "Default Header"}
        {@render children()}
    </div>
    ```

*   **Components are no longer classes**:

    * Instead of `new MyComponent(...)`, use `mount(MyComponent, ...)` or `hydrate(MyComponent, ...)`

**2. Runes in Detail:**

*   **`$state()`:** Declares reactive state.  Any changes to variables declared with `$state()` will trigger updates in the component. It creates a deeply reactive proxy, unless `$state.raw` is used.

    ```svelte
    <script>
    let count = $state(0);
    </script>
    <p>{count}</p>
    <button onclick={() => count += 1}>Increment</button>
    ```

*   **`$derived()`:**  Declares a value that is derived from other reactive values. The derived value is automatically updated whenever its dependencies change.

    ```svelte
    <script>
    let count = $state(0);
    let doubled = $derived(count * 2);
    </script>
    <p>{doubled}</p>
    ```

*   **`$effect()`:**  Executes a side effect when its dependencies change.  Use this for things like DOM manipulation, calling external libraries, or logging. Effects run after the DOM has updated.

    ```svelte
    <script>
    let count = $state(0);
    $effect(() => {
        console.log("Count is now", count);
    });
    </script>
    ```

*   **`$props()`:**  Declares component properties.  Use destructuring to extract the properties and provide default values.

    ```svelte
    <script>
    let { name = "World", age } = $props();
    </script>
    <h1>Hello, {name}!</h1>
    ```

* `$bindable()`: Marks a prop as bindable, meaning changes in the child component flow back up to the parent.

```svelte
    <script>
        let { value = $bindable() } = $props();
    </script>

    <input bind:value={value} />
```

Transitions and Animations:**

*   **`in:` and `out:` Directives:** These directives are used to specify transitions that occur when an element enters or leaves the DOM, respectively. They are unidirectional, meaning that an `in` transition will play alongside an `out` transition if the element is removed while the `in` transition is still in progress. If the out transition is aborted, transitions will restart from scratch. This is contrast to `transition:`, which is bidirectional.

    ```svelte
    <script>
      import { fade, fly } from 'svelte/transition';
    let visible = $state(false);
    </script>

    {#if visible}
    	<div in:fly={{ y: 200 }} out:fade>flies in, fades out</div>
    {/if}
    ```

*   **`animate:` Directive:** This directive triggers an animation when the contents of a keyed `{#each}` block are reordered. The directive must be placed on the immediate child of the `{#each}` block. Animations do not run when elements are added or removed, only when their index changes.

    ```svelte
    {#each list as item, index (item)}
    	<li animate:flip>{item}</li>
    {/each}
    ```

    Custom animation functions can be used to define the animation. These functions receive the animated node, the start and end DOMRects, and any specified parameters.  The function returns a `css` function or `tick` function which defines the animation's behavior.

    ```svelte
    <script>
    import { cubicOut } from 'svelte/easing';

    function whizz(node, { from, to }, params) {
    	const dx = from.left - to.left;
    	const dy = from.top - to.top;

    	const d = Math.sqrt(dx * dx + dy * dy);

    	return {
    		delay: 0,
    		duration: Math.sqrt(d) * 120,
    		easing: cubicOut,
    		css: (t, u) => `transform: translate(${u * dx}px, ${u * dy}px) rotate(${t * 360}deg);`
    	};
    }
    let list = $state(['one','two','three'])
    </script>

    {#each list as item, index (item)}
    	<div animate:whizz>{item}</div>
    {/each}
    ```

**Styling:**

*   **`style:` Directive:** This provides a shorthand for setting multiple styles on an element. Styles set using this directive take precedence over those set using the `style` attribute. The `|important` modifier can be used to mark a style as important.

    ```svelte
    <div style:color="red" style:width="12rem" style:background-color={darkMode ? 'black' : 'white'}>...</div>
    ```

*   **`class` Attribute:**  Since Svelte 5.16, `class` can be an object or array and is converted to a string using `clsx`. If it's an object, the truthy keys are added as classes. If it's an array, truthy values are combined. This is particularly useful with Tailwind CSS.

    ```svelte
    <script>
    	let { cool } = $props();
    </script>

    <div class={{ cool, lame: !cool }}>...</div>
    <div class={[faded && 'saturate-0 opacity-50', large && 'scale-200']}>...</div>
    ```

*   **`class:` Directive:**  (Prior to Svelte 5.16) A way to set classes conditionally, but now less common with the object/array syntax for the `class` attribute.

    ```svelte
    <div class:cool={cool} class:lame={!cool}>...</div>
    ```

**Control Flow:**

*   **`{#if ...}`:** Conditionally renders content.
*   **`{#each ...}`:** Iterates over arrays, array-like objects, or iterables.  Keys should be used for efficient updates of keyed blocks.
*   **`{#await ...}`:**  Handles promises with `{:then}` and `{:catch}` blocks.

**Data Fetching:**

*   The simplest data fetching can be done using the built-in `fetch` method.
*   `{#await}` blocks allow you to branch on the states of a Promise - pending, fulfilled, or rejected.
*   SvelteKit offers a data-loading approach with its router.

**Special Elements:**

*   **`<svelte:boundary>`:** Enables error boundaries. If a `failed` snippet is provided, it renders with the error and a `reset` function.  The `onerror` function can be used to report errors.
*   **`<svelte:window>`:** Allows adding event listeners to the `window` object and binding to window properties.
*   **`<svelte:document>`:** Allows adding event listeners to the `document` object.
*   **`<svelte:body>`:** Allows adding event listeners to the `document.body` object.
*   **`<svelte:head>`:** Allows inserting elements into the `document.head`.
*   **`<svelte:element>`:** Allows rendering elements with tag names determined dynamically at runtime. It is recommended you always capitalize if it is a component
*   **`<svelte:options>`:** Allows specifying per-component compiler options.

Stores:**

*   Stores are objects with a `subscribe` method, enabling reactive access to values. The file focuses on `svelte/store`'s implementations but emphasizes the use of runes for reactivity in Svelte 5 when possible.

    *   `writable`: Creates a store whose values can be set from 'outside' the component. You set the new value by calling the `.set()` method on the variable (e.g., `count.set(5)`). You can also update the value by calling `.update()` method (e.g., `count.update(n => n + 1)`).

        ```javascript
        import { writable } from 'svelte/store';

        const count = writable(0);

        count.subscribe((value) => {
        	console.log(value);
        });

        count.set(1);

        count.update((n) => n + 1);
        ```

    *   `readable`:  Creates a store that can't be set 'outside'. Similar to `writable`, but is configured at start with a set method only.

        ```javascript
        import { readable } from 'svelte/store';

        const time = readable(new Date(), (set) => {
        	set(new Date());

        	const interval = setInterval(() => {
        		set(new Date());
        	}, 1000);

        	return () => clearInterval(interval);
        });
        ```

    *   `derived`: Create a store whose value depends on another store. It takes an array of stores, and a function. Every time one of the dependency stores updates, the passed in function is run and is value is then set to this store.

        ```javascript
        import { derived } from 'svelte/store';

        const summed = derived([storeA, storeB], ([$storeA, $storeB]) => {
        	return $storeA + $storeB;
        });
        ```

*   It is now recommended to use runes instead of stores for component-level state and derived values where possible.
*   `fromStore` and `toStore` - these methods are not particularly relevant to Svelte 5, runes-based development. They help bridge Svelte 3/4 stores with custom store implementations, but are effectively rendered obsolete by runes.

**Context:**

*   Context allows sharing data between a component and its descendants. It emphasizes that this is a component-scoped, not global, mechanism.
*   `setContext(key, value)`: Sets a context variable.
*   `getContext(key)`: Retrieves a context variable.
*   `hasContext(key)`: Checks if a context key exists.
* `getAllContexts()`: gets all contexts in an object.
*  Context is not inherently reactive; reactive values can be passed in through `$state` objects.

    ```svelte
    <script>
    	import { setContext, getContext } from 'svelte';
    let count = $state(0);
    setContext('count', count)
    </script>
    ```

**Lifecycle Hooks:**

*   **`onMount`:**  Schedules a callback to run after the component is mounted. Returns a function that will be called when the component is unmounted. It emphasizes that these hooks do _not_ run during server-side rendering. Should be used sparingly. Is a synchronous API.
*   **`onDestroy`:** Schedules a callback to run before the component is unmounted.
*   **`tick`:**  Returns a promise that resolves after any pending state changes have been applied. This can be used to interact with the DOM after the state changes. This is used to force updates before `$effect` and `$effect.pre`.
*   `beforeUpdate` and `afterUpdate` are deprecated and should be replaced with `$effect.pre` and `$effect` respectively.

**Imperative Component API:**

*   This section covers the `mount`, `hydrate`, `render`, and `unmount` functions.
* Emphasizes `flushSync()` after `mount` and `hydrate` calls, should you require to.

**Testing:**

*   Recommend using vitest for unit and integration testing
*   It is possible to test components in isolation using jsdom

**TypeScript:**

*   Typescript needs to include lang="ts" in order to work
*   You can define Prop types as you would normally do
* You can use generics to create dynamic components

**Custom Elements:**

* You can add custom element tag with `<svelte:options customElement="my-custom-element" />`
* Provides a series of caveats for using custom elements.


Reactivity in depth**

*   There isn't a specific "Reactivity in Depth" section yet, but the key takeaway is to use runes (`$state`, `$derived`, `$effect`) to manage reactivity explicitly.

**Reference: svelte**

*   **`SvelteComponent` & `SvelteComponentTyped`:** These are obsolete in Svelte 5. Use the `Component` type instead. Code that used these for component definitions should be updated.

    ```ts
    // Before (Svelte 4)
    import { SvelteComponentTyped } from 'svelte';
    export class MyComponent extends SvelteComponentTyped<{ foo: string }> {}

    // After (Svelte 5)
    import type { Component } from 'svelte';
    export const MyComponent: Component<{ foo: string }>; // = ...implementation
    ```

*   **`beforeUpdate` & `afterUpdate`:** Deprecated in favor of `$effect.pre` and `$effect`. Code that relies on these for DOM manipulation should be migrated.

    ```svelte
    <script>
    import { beforeUpdate, afterUpdate } from 'svelte';

    beforeUpdate(() => {
    	// code to run before the component updates
    });

    afterUpdate(() => {
    	// code to run after the component updates
    });
    </script>

    // Svelte 5
    <script>
    $effect.pre(() => {
        // code to run before the component updates
    });

    $effect(() => {
        // code to run after the component updates
    });
    </script>
    ```

*   **`createEventDispatcher`:** Deprecated in favor of callback props.

    ```svelte
    // Before
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();
    dispatch('someEvent', { detail: someValue });

    // After
    let { onSomeEvent } = $props(); // or similar
    onSomeEvent(someValue);
    ```

*   **`getAllContexts`, `getContext`, `hasContext`, `setContext`:**  These context functions are still valid, but remember to use reactive objects inside the context for reactivity.

    ```svelte
    // setting a context
    <script>
        import { setContext } from 'svelte';

        let myReactiveValue = $state(0)
        setContext('someKey', myReactiveValue)

    </script>

    //consuming it
    <script>
        import { getContext } from 'svelte';

        const contextValue = getContext('someKey'); // access it in an object now
    </script>
    ```

*   **`hydrate`, `mount`, `unmount`:**  Still the correct way to instantiate, hydrate and destory your component.

*   **`tick`**: Use this function inside a `$effect.pre` callback and call the async function. This will allow you to update the DOM before performing side effects.

*   `untrack`: Use to prevent a dependency for $derived or $effect.

**Reference: svelte/action:**

*   The `Action` and `ActionReturn` types are still relevant. However, the signature of `Action` is slightly different.

    ```ts
    // Old
    const myAction: Action = (node, parameters) => { ... }

    // New
    const myAction: Action<HTMLElement, string> = (node, parameters) => { ... }
    ```

**Reference: svelte/animate**

*   The animation functions and types remain largely the same.

**Reference: svelte/compiler:**

*   `compile`, `compileModule`, `migrate`, `parse`, and `preprocess` and helper functions are all useful for building Svelte tooling, which is unlikely to be a day-to-day use case.

**Reference: svelte/easing:**

* All Easing Functions are the same.

**Reference: svelte/events**

*   The `on` function is still useful for adding event listeners to the window and document.

**Reference: svelte/legacy:**

*   This entire module is for backwards compatibility and should be avoided in new Svelte 5 projects using runes. If you see these in your code, you should migrate off of them.

**Reference: svelte/motion:**

* `Spring` and `Tween` are useful classes for managing animation of state, but the original store implementations (`spring`, `tweened`) are legacy and should be used with caution. It is also important to note that they are only avialable as of Svelte 5.8
* `prefersReducedMotion` is useful for respecting user preferences for reduced motion.

**Reference: svelte/reactivity/window:**

* Can use the built in state, e.g. innerHeight, innerWidth etc.


# Several useful concrete examples and specific patterns

1. Deep Reactivity Example for `$state`:** The `todos` array example clearly demonstrates how `$state` makes nested properties reactive and how array methods like `push` trigger updates. This is more illustrative than just saying 1`$state` creates a deep proxy.
    ```svelte /dev/null/example.svelte#L1-20
    <script>
        let todos = $state([
            { done: false, text: 'Learn Svelte' },
            { done: false, text: 'Build an app' }
        ]);

        function toggle(index) {
            todos[index].done = !todos[index].done; // Reactivity applies to individual items
        }
    </script>

    <ul>
        {#each todos as todo, index}
            <li>
                <input type="checkbox" bind:checked={todo.done} onclick={() => toggle(index)} />
                {todo.text}
            </li>
        {/each}
    </ul>

    <button onclick={() => todos.push({ done: false, text: 'New task' })}>
        Add Todo
    </button>
    ```

2.  **Practical `$effect` Example:** The canvas example provides a much better illustration of a real-world side effect (DOM manipulation based on state) compared to the simple `console.log`.
    ```svelte /dev/null/example.svelte#L1-18
    <script>
        let size = $state(50);
        let color = $state('#ff3e00');
        let canvas;

        $effect(() => {
            const context = canvas.getContext('2d');
            context.clearRect(0, 0, canvas.width, canvas.height);

            // This effect runs whenever `color` or `size` changes
            context.fillStyle = color;
            context.fillRect(0, 0, size, size);
        });
    </script>

    <canvas bind:this={canvas} width="100" height="100" />

    <input type="color" bind:value={color} />
    <input type="range" bind:value={size} min="10" max="100" />
    ```

3.  **`$derived` vs. `$effect` Pitfall:** The example explicitly showing *not* to use `$effect` for derived state is valuable for preventing common errors.
    ```svelte /dev/null/example.svelte#L1-12
    <script>
        let count = $state(0);
        let doubled = $derived(count * 2); // Correct approach

        // Incorrect approach (causes infinite loops):
        // $effect(() => {
        //   doubled = count * 2; // Don't modify state tracked by the effect within the effect!
        // });
    </script>

    <h1>{count} doubled is {doubled}</h1>

    <button onclick={() => count += 1}>Increment</button>
    ```

4.  **`$derived.by` Example:** The guide mentions `$derived` but doesn't show the `.by` function for more complex, multi-step derivations.
    ```svelte /dev/null/example.svelte#L1-16
    <script lang="ts">
        let numbers = $state([1, 2, 3]);

        // `total` is automatically recalculated when `numbers` change
        let total = $derived.by(() => {
            let sum = 0;
            for (const n of numbers) {
                sum += n;
            }
            return sum;
        });
    </script>

    <button onclick={() => numbers.push(numbers.length + 1)}>
        Add Number
    </button>

    <p>{numbers.join(' + ')} = {total}</p>
    ```

5.  **Component Communication via Callbacks:** While the guide mentions this replaces `createEventDispatcher`, the explicit parent/child example with `inflate`/`deflate` callbacks makes the pattern much clearer.
    *Parent:*
    ```svelte /dev/null/Parent.svelte#L1-25
    <script lang="ts">
      import Pump from './Pump.svelte';

      let size = $state(15);
      let burst = $state(false);

      function reset() {
        size = 15;
        burst = false;
      }
    </script>

    <Pump
      inflate={(power) => { // Callback prop
        size += power;
        if (size > 75) burst = true;
      }}
      deflate={(power) => { // Callback prop
        if (size > 0) size -= power;
      }}
    />

    {#if burst}
      <button onclick={reset}>new balloon</button>
      <span class="boom">💥</span>
    {:else}
      <span class="balloon" style="scale: {0.01 * size}">
        🎈
      </span>
    {/if}
    ```
    *Child (`Pump.svelte`):*
    ```svelte /dev/null/Pump.svelte#L1-10
    <script lang="ts">
      // Declare the expected callback props
      let { inflate, deflate } = $props<{ inflate: (power: number) => void, deflate: (power: number) => void }>();
      let power = $state(5);
    </script>

    <button onclick={() => inflate(power)}>inflate</button>
    <button onclick={() => deflate(power)}>deflate</button>

    <button onclick={() => power--}>-</button>
    Pump power: {power}
    <button onclick={() => power++}>+</button>
    ```

6.  **`$bindable` Full Example:** The guide explains `$bindable` but showing both the child component declaring it and the parent component using `bind:value` makes the two-way binding clearer.
    *Child:*
    ```svelte /dev/null/FancyInput.svelte#L1-5
    <script lang="ts">
        // value is optional, defaults to a bindable signal, forward other props
        let { value = $bindable(), ...props } = $props();
    </script>

    <input bind:value={value} {...props} />
    ```
    *Parent:*
    ```svelte /dev/null/Parent.svelte#L1-7
    <script lang="ts">
        import FancyInput from './FancyInput.svelte';

        let message = $state('hello');
    </script>

    <FancyInput bind:value={message} /> <!-- Binds parent's `message` to child's `value` -->
    <p>{message}</p>
    ```

7.  **Basic TypeScript Example:** A simple, complete component showing `<script lang="ts">` and basic type usage would be a good addition to the TypeScript section.
    ```svelte /dev/null/TsExample.svelte#L1-9
    <script lang="ts">
        let name: string = 'world';

        function greet(name: string) {
            alert(`Hello, ${name}!`);
        }
    </script>

    <button onclick={() => greet(name)}>Greet</button>
    ```

8.  **Combining Multiple Event Handlers:** Explicitly showing how to call multiple functions from a single event attribute is a useful pattern.
    ```svelte /dev/null/example.svelte#L1-8
    <script>
        function one(e) { console.log('one', e); }
        function two(e) { console.log('two', e); }
    </script>
    <button
      onclick={(e) => {
        one(e);
        two(e);
      }}
    >...</button>
    ```
