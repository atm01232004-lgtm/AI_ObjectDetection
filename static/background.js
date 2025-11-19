const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');

let particlesArray;

// Cấu hình canvas full màn hình
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Xử lý khi thay đổi kích thước màn hình
window.addEventListener('resize', function() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    init();
});

// Tạo hạt (Particle)
class Particle {
    constructor(x, y, directionX, directionY, size, color) {
        this.x = x;
        this.y = y;
        this.directionX = directionX;
        this.directionY = directionY;
        this.size = size;
        this.color = color;
    }

    // Vẽ hạt
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.fill();
    }

    // Cập nhật vị trí hạt
    update() {
        // Kiểm tra va chạm cạnh màn hình
        if (this.x > canvas.width || this.x < 0) {
            this.directionX = -this.directionX;
        }
        if (this.y > canvas.height || this.y < 0) {
            this.directionY = -this.directionY;
        }

        // Di chuyển
        this.x += this.directionX;
        this.y += this.directionY;

        this.draw();
    }
}

// Khởi tạo mảng hạt
function init() {
    particlesArray = [];
    // Số lượng hạt phụ thuộc vào diện tích màn hình
    let numberOfParticles = (canvas.height * canvas.width) / 9000;

    for (let i = 0; i < numberOfParticles; i++) {
        let size = (Math.random() * 2) + 1; // Kích thước ngẫu nhiên
        let x = (Math.random() * ((innerWidth - size * 2) - (size * 2)) + size * 2);
        let y = (Math.random() * ((innerHeight - size * 2) - (size * 2)) + size * 2);
        let directionX = (Math.random() * 2) - 1; // Tốc độ X (-1 đến 1)
        let directionY = (Math.random() * 2) - 1; // Tốc độ Y
        let color = '#88CDF6'; // Màu hạt (Xanh nhạt theo theme của bạn)

        particlesArray.push(new Particle(x, y, directionX, directionY, size, color));
    }
}

// Nối các hạt lại với nhau nếu chúng ở gần
function connect() {
    let opacityValue = 1;
    for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a; b < particlesArray.length; b++) {
            let distance = ((particlesArray[a].x - particlesArray[b].x) * (particlesArray[a].x - particlesArray[b].x)) +
                           ((particlesArray[a].y - particlesArray[b].y) * (particlesArray[a].y - particlesArray[b].y));

            // Nếu khoảng cách < 140px thì vẽ đường nối
            if (distance < (canvas.width/7) * (canvas.height/7)) {
                opacityValue = 1 - (distance / 20000);
                ctx.strokeStyle = 'rgba(136, 205, 246,' + opacityValue + ')'; // Màu dây nối
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                ctx.stroke();
            }
        }
    }
}

// Vòng lặp Animation
function animate() {
    requestAnimationFrame(animate);
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
    }
    connect();
}

// Chạy ngay đi
init();
animate();