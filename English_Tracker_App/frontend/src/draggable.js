export function draggable(node, handleClass) {
  let x = 0;
  let y = 0;
  let startX = 0;
  let startY = 0;
  let isDragging = false;
  let hasDragged = false;

  function handleMousedown(event) {
    if (handleClass && !event.target.closest(`.${handleClass}`)) {
      return; // Only drag if clicking the handle
    }
    
    startX = event.clientX - x;
    startY = event.clientY - y;
    isDragging = true;
    hasDragged = false;
    
    window.addEventListener('mousemove', handleMousemove);
    window.addEventListener('mouseup', handleMouseup);
  }

  function handleMousemove(event) {
    if (!isDragging) return;
    hasDragged = true;
    x = event.clientX - startX;
    y = event.clientY - startY;
    node.style.transform = `translate(${x}px, ${y}px)`;
  }

  function handleMouseup(event) {
    isDragging = false;
    window.removeEventListener('mousemove', handleMousemove);
    window.removeEventListener('mouseup', handleMouseup);
    
    // If we dragged, prevent click events from firing on the element
    if (hasDragged) {
      setTimeout(() => { hasDragged = false; }, 0);
    }
  }

  function handleClick(event) {
    if (hasDragged) {
      event.stopPropagation();
      event.preventDefault();
    }
  }

  node.addEventListener('mousedown', handleMousedown);
  node.addEventListener('click', handleClick, true); // Use capture phase

  if (handleClass) {
    // Add grab cursor to the handle(s)
    const handles = node.querySelectorAll(`.${handleClass}`);
    handles.forEach(h => h.style.cursor = 'grab');
  } else {
    node.style.cursor = 'grab';
  }

  return {
    destroy() {
      node.removeEventListener('mousedown', handleMousedown);
      node.removeEventListener('click', handleClick, true);
    }
  };
}
