using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using B7KHSX.Api.Data;
using B7KHSX.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Database — SQLite for dev, PostgreSQL for production
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (!string.IsNullOrEmpty(connectionString) && !connectionString.Contains("YOUR_PASSWORD_HERE"))
{
    // PostgreSQL (production)
    builder.Services.AddDbContext<AppDbContext>(options =>
        options.UseNpgsql(connectionString));
}
else
{
    // SQLite (development fallback)
    var dbPath = Path.Combine(AppContext.BaseDirectory, "b7khsx_dev.db");
    builder.Services.AddDbContext<AppDbContext>(options =>
        options.UseSqlite($"Data Source={dbPath}"));
}

// JWT Authentication
var jwtKey = builder.Configuration["Jwt:Key"] ?? "B7KHSX_SuperSecretKey_2024_Production_Planning_System_Key!";
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"] ?? "B7KHSX",
            ValidAudience = builder.Configuration["Jwt:Audience"] ?? "B7KHSX-Client",
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
        };
    });

builder.Services.AddAuthorization();

// Services
builder.Services.AddScoped<AuthService>();

// Controllers
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("http://localhost:5173", "http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

// Auto-create database on startup
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowFrontend");
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
